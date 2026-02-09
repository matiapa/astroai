"""
Controller for the /analyze endpoint.
"""

import asyncio
import os
import uuid
import base64
import json
import io
from PIL import Image

from fastapi import UploadFile

from src.tools.capture_sky.tool import SkyCaptureTool
from src.tools.capture_sky.gemini_identifier import GeminiStructureIdentifier
from src.tools.capture_sky.simbad_query import query_simbad_by_id
from src.services.narration_generator import NarrationGenerator
from src.services.tts_service import TTSService
from src.config import get_config_from_env


# Directory for temporary audio files


def _ensure_audios_dir() -> str:
    config = get_config_from_env()
    audios_dir = os.path.join(config.storage_dir, "audios")

    """Ensure audios directory exists and return its path."""
    os.makedirs(audios_dir, exist_ok=True)
    return audios_dir


async def analyze_image_stream(
    image: UploadFile,
    language: str,
    base_url: str
):
    """
    Analyze an astronomical image and yield progress updates via SSE.
    
    Args:
        image: Uploaded image file
        language: ISO language code for narration
        base_url: Base URL for constructing audio download URLs
    
    Yields:
        Dict with "event" and "data" for SSE:
        - analyzing_image: starts analysis
        - analysis_complete: plate_solving + identified_objects
        - narration_complete: title + text
        - audio_complete: audio_url (final event)
        - error: on failure
    """
    try:
        # Read image and encode to base64 for SkyCaptureTool
        image_bytes = await image.read()
        image_base64 = base64.b64encode(image_bytes).decode("utf-8")
        
        # Step 1: Analyze the image
        yield {"event": "analyzing_image", "data": "{}"}
        print("> Step 1: Analyzing image with SkyCaptureTool...")
        
        sky_tool = SkyCaptureTool()
        analysis_result = await asyncio.to_thread(sky_tool.capture_sky, image_base64)
        
        if not analysis_result.get("success"):
            yield {"event": "error", "data": json.dumps({"error": analysis_result.get("error", "Image analysis failed")})}
            return
        
        plate_solving = analysis_result.get("plate_solving", {})
        identified_objects = analysis_result.get("identified_objects", [])
        
        # Step 1.5: Identify main structure with Gemini
        print("> Step 1.5: Identifying main structure with Gemini...")
        try:
            gemini_identifier = GeminiStructureIdentifier(get_config_from_env())
            # We need a PIL image for Gemini
            pil_image = Image.open(io.BytesIO(image_bytes))
            
            main_structure = await asyncio.to_thread(
                gemini_identifier.identify_main_structure,
                pil_image,
                identified_objects,
                plate_solving
            )
            
            if main_structure:
                main_name = main_structure.get("name")
                print(f"  Gemini identified main structure: {main_name}")
                
                # Query SIMBAD for details
                config = get_config_from_env()
                simbad_obj = await asyncio.to_thread(query_simbad_by_id, main_name, config)
                
                if simbad_obj:
                     # Calculate radius if missing in SIMBAD but present in Gemini
                     radius_arcsec = simbad_obj.position.radius_arcsec
                     pixel_coords = main_structure.get("pixel_coords", {})
                     
                     if (not radius_arcsec or radius_arcsec == 0) and "radius_pixels" in pixel_coords:
                         if plate_solving.get("pixel_scale_arcsec"):
                             radius_arcsec = pixel_coords["radius_pixels"] * plate_solving["pixel_scale_arcsec"]
                    
                     structure_dict = {
                        "name": simbad_obj.name,
                        "type": simbad_obj.catalog,
                        "subtype": simbad_obj.object_type_description,
                        "celestial_coords": {
                            "ra_deg": round(simbad_obj.position.ra, 6),
                            "dec_deg": round(simbad_obj.position.dec, 6),
                            "radius_arcsec": round(radius_arcsec, 2),
                        },
                        "pixel_coords": pixel_coords,
                        "confidence": main_structure.get("confidence", 1.0)
                     }
                     
                     # Add optional fields
                     if simbad_obj.alternative_names:
                         structure_dict["alternative_names"] = simbad_obj.alternative_names
                     if simbad_obj.magnitude_visual:
                         structure_dict["magnitude_visual"] = round(simbad_obj.magnitude_visual, 2)
                     if simbad_obj.distance_lightyears:
                         structure_dict["distance_lightyears"] = simbad_obj.distance_lightyears
                     if simbad_obj.bv_color_index:
                         structure_dict["bv_color_index"] = round(simbad_obj.bv_color_index, 2)
                     if simbad_obj.spectral_type:
                         structure_dict["spectral_type"] = simbad_obj.spectral_type
                     if simbad_obj.morphological_type:
                         structure_dict["morphological_type"] = simbad_obj.morphological_type

                     # Insert at the beginning!
                     identified_objects.insert(0, structure_dict)
                else:
                    print(f"  Could not find '{main_name}' in SIMBAD.")
            else:
                print("  Gemini did not identify a specific main structure.")
                
        except Exception as e:
            print(f"  Error in Gemini step: {e}")
            import traceback
            traceback.print_exc()

        # Yield analysis results
        yield {
            "event": "analysis_complete",
            "data": json.dumps({
                "plate_solving": plate_solving,
                "identified_objects": identified_objects
            })
        }
        
        # Step 2: Generate narration
        yield {"event": "generating_narration", "data": "{}"}
        print(f"> Step 2: Generating narration in '{language}'...")
        
        narration_gen = NarrationGenerator()
        narration_result = await asyncio.to_thread(
            narration_gen.generate,
            plate_solving,
            identified_objects,
            language
        )
        
        # Merge legends into identified objects
        object_legends = narration_result.get("object_legends", {})
        for obj in identified_objects:
            obj_name = obj.get("name", "")
            if obj_name in object_legends:
                obj["legend"] = object_legends[obj_name]
        
        # Yield narration results
        yield {
            "event": "narration_complete",
            "data": json.dumps({
                "title": narration_result.get("title", "The Night Sky"),
                "text": narration_result.get("text", ""),
                "object_legends": object_legends
            })
        }
        
        # Step 3: Generate TTS audio
        yield {"event": "generating_audio", "data": "{}"}
        print("> Step 3: Generating TTS audio...")
        
        tts_service = TTSService(language=language)
        
        # Generate unique filename for audio
        audio_filename = f"narration_{uuid.uuid4().hex[:8]}.wav"
        audios_dir = _ensure_audios_dir()
        audio_output_path = os.path.join(audios_dir, audio_filename)
        
        _, saved_path = await asyncio.to_thread(
            tts_service.generate_audio,
            narration_result.get("text", ""),
            audio_output_path
        )
        
        # Build audio URL
        audio_url = f"{base_url}/audio/{audio_filename}"
        
        # Yield audio URL (final event)
        yield {
            "event": "audio_complete",
            "data": json.dumps({"audio_url": audio_url})
        }
        
        print("> Analysis complete!")
        
    except Exception as e:
        print(f"Error during analysis: {e}")
        import traceback
        traceback.print_exc()
        yield {"event": "error", "data": json.dumps({"error": str(e)})}
