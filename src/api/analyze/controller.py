"""
Controller for the /analyze endpoint.
"""

import os
import uuid
import base64
from typing import Optional

from fastapi import UploadFile

from src.tools.capture_sky.tool import SkyCaptureTool
from src.services.narration_generator import NarrationGenerator
from src.services.tts_service import TTSService
from src.api.analyze.dto import (
    AnalyzeResponse,
    PlateSolving,
    Narration,
    IdentifiedObject,
)


# Directory for temporary audio files
TMP_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "tmp")


def _ensure_tmp_dir() -> str:
    """Ensure tmp directory exists and return its path."""
    os.makedirs(TMP_DIR, exist_ok=True)
    return TMP_DIR


async def analyze_image(
    image: UploadFile,
    language: str,
    base_url: str
) -> AnalyzeResponse:
    """
    Analyze an astronomical image.
    
    Args:
        image: Uploaded image file
        language: ISO language code for narration
        base_url: Base URL for constructing audio download URLs
    
    Returns:
        AnalyzeResponse with analysis results
    """
    try:
        # Read image and encode to base64 for SkyCaptureTool
        image_bytes = await image.read()
        image_base64 = base64.b64encode(image_bytes).decode("utf-8")
        
        # Step 1: Analyze the image with SkyCaptureTool
        print("> Step 1: Analyzing image with SkyCaptureTool...")
        sky_tool = SkyCaptureTool()
        analysis_result = sky_tool.capture_sky(image_base64)
        
        if not analysis_result.get("success"):
            return AnalyzeResponse(
                success=False,
                error=analysis_result.get("error", "Image analysis failed")
            )
        
        plate_solving = analysis_result.get("plate_solving", {})
        identified_objects = analysis_result.get("identified_objects", [])
        
        # Step 2: Generate narration with specified language
        print(f"> Step 2: Generating narration in '{language}'...")
        narration_gen = NarrationGenerator()
        narration_result = narration_gen.generate(
            plate_solving=plate_solving,
            identified_objects=identified_objects,
            language=language
        )
        
        # Step 3: Generate TTS audio
        print("> Step 3: Generating TTS audio...")
        tts_service = TTSService(language=language)
        
        # Generate unique filename for audio
        audio_filename = f"narration_{uuid.uuid4().hex[:8]}.wav"
        tmp_dir = _ensure_tmp_dir()
        audio_output_path = os.path.join(tmp_dir, audio_filename)
        
        _, saved_path = tts_service.generate_audio(
            text=narration_result.get("text", ""),
            output_path=audio_output_path
        )
        
        # Build audio URL
        audio_url = f"{base_url}/audio/{audio_filename}"
        
        # Step 4: Merge legends into identified objects
        print("> Step 4: Building response...")
        object_legends = narration_result.get("object_legends", {})
        for obj in identified_objects:
            obj_name = obj.get("name", "")
            if obj_name in object_legends:
                obj["legend"] = object_legends[obj_name]
        
        # Build response
        return AnalyzeResponse(
            success=True,
            plate_solving=PlateSolving(**plate_solving),
            narration=Narration(
                title=narration_result.get("title", "The Night Sky"),
                text=narration_result.get("text", ""),
                audio_url=audio_url
            ),
            identified_objects=[
                IdentifiedObject(**obj) for obj in identified_objects
            ]
        )
        
    except Exception as e:
        print(f"Error during analysis: {e}")
        import traceback
        traceback.print_exc()
        return AnalyzeResponse(
            success=False,
            error=str(e)
        )
