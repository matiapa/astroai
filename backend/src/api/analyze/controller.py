"""
Controller for the /analyze endpoint.
"""

import asyncio
import os
import uuid
import base64
import json

from fastapi import UploadFile

from src.tools.capture_sky.tool import SkyCaptureTool
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
