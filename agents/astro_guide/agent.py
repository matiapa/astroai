#!/usr/bin/env python3
"""
AstroGuide - An AI-powered astronomical tour guide agent.

This agent acts as an expert astronomer providing engaging "tourist information"
about celestial objects visible through a telescope. It captures images from a webcam, uses plate solving and 
object detection, then combines this data with its knowledge and web searches to create 
fascinating narratives about what the user is seeing.
"""

import sys
import io
from pathlib import Path
from typing import Optional

import google.genai.types as types
from google.adk.tools import FunctionTool

# Add project root to path so we can import from src
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from google.adk.agents import Agent
from google.adk.tools import google_search

from tools.analyze_image.analyze_image_tool import analyze_image


def capture_and_analyze_sky() -> dict:
    """
    Captures an image from the telescope camera and analyzes it to identify celestial objects.
    
    This tool captures a live image from the connected webcam/camera, performs plate solving 
    to determine exact sky coordinates, detects visible celestial objects in the image, and 
    queries SIMBAD to identify each detected object.    
    Returns:
        A dictionary containing:
        - success: Whether the analysis succeeded
        - error: Error message if success is False
        - captured_image: types.Part with raw image captured from webcam (for LLM vision)
        - annotated_image: types.Part with annotated image showing objects marked and labeled (for LLM vision)
        - plate_solving: Sky coordinates of the image center (RA/DEC), field of view, pixel scale
        - objects: Dictionary with:
            - identified_count: Number of objects identified via SIMBAD
            - identified: List of identified objects with:
                - name: Object designation (e.g., "HD 127838", "M42")
                - type: Category (Star, Messier, NGC/IC, Deep Sky)
                - subtype: Specific type (Be Star, Variable Star, Galaxy, etc.)
                - magnitude_v: Visual magnitude (lower = brighter)
                - bv_color_index: B-V color index (temperature indicator)
                - spectral_type: For stars, their spectral classification (e.g., "G2V", "B1Ib")
                - morphological_type: For galaxies, Hubble classification
                - distance_lightyears: Distance from Earth
            - unidentified_count: Number of detected objects not found in SIMBAD
            - unidentified: List of unidentified detections with coordinates
    
    Example result:
        {
            "success": True,
            "captured_image": <types.Part with image/png>,
            "annotated_image": <types.Part with image/png>,
            "plate_solving": {
                "center": {"ra_deg": 220.33, "dec_deg": -60.6, "ra_hms": "14h 41m 20s", "dec_dms": "-60° 35' 56\""},
                "field_of_view": {"width_arcmin": 56.7, "height_arcmin": 56.8}
            },
            "objects": {
                "identified_count": 29,
                "identified": [
                    {"name": "HD 127838", "type": "Star", "magnitude_v": 9.17, "spectral_type": "B1Ib/II", "distance_lightyears": 7716.0},
                    {"name": "HD 128016", "type": "Star", "subtype": "Double or Multiple Star", "magnitude_v": 8.69},
                    ...
                ],
                "unidentified_count": 0
            }
        }
    """
    # Call the analyze_image function which captures from webcam
    result = analyze_image(verbose=False)  # Suppress logs when used as agent tool
    
    # Convert images to types.Part for proper multimodal handling
    # This allows Gemini to actually "see" the images using its vision capabilities
    if result.get("success"):
        for key in ["captured_image", "annotated_image"]:
            if result.get(key):
                try:
                    buffered = io.BytesIO()
                    result[key].save(buffered, format="PNG")
                    # Create a types.Part with inline binary data
                    result[key] = types.Part.from_bytes(
                        data=buffered.getvalue(),
                        mime_type="image/png"
                    )
                except Exception as e:
                    result[key] = None
                    result[f"{key}_error"] = f"Failed to encode image: {str(e)}"
    
    return result

capture_and_analyze_sky_tool = FunctionTool(func=capture_and_analyze_sky)

# Read the prompt from the markdown file
with open("./agents/astro_guide/prompt.md", "r") as f:
    prompt = f.read()

# Define the root agent
root_agent = Agent(
    model="gemini-3-flash-preview",
    name="astro_guide",
    description="Un astrónomo experto y guía turístico del cielo que captura imágenes del telescopio y brinda narrativas fascinantes sobre los objetos celestes.",
    instruction=prompt,
    tools=[
        capture_and_analyze_sky_tool,
        # google_search,
    ],
)
