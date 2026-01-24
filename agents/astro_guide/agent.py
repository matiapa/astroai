#!/usr/bin/env python3
"""
AstroGuide - An AI-powered astronomical tour guide agent.

This agent acts as an expert astronomer providing engaging "tourist information"
about celestial objects visible through a telescope. It captures images from a webcam, uses plate solving and catalog 
queries, then combines this data with its knowledge and web searches to create 
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


def capture_and_analyze_sky(
    search_radius: Optional[float] = None,
    magnitude_limit: Optional[float] = 8.0
) -> dict:
    """
    Captures an image from the telescope camera and analyzes it to identify celestial objects.
    
    This tool captures a live image from the connected webcam/camera, then performs plate solving to determine exact sky coordinates 
    and queries astronomical databases to identify all visible celestial objects.
        
    Args:
        search_radius: Search radius in degrees for finding objects. 
                      If not provided, it's auto-calculated from the field of view.
        magnitude_limit: Only include objects brighter than this magnitude (default: 8.0).
                        Lower values = fewer but brighter objects.
                        Higher values = more objects including fainter ones.
    
    Returns:
        A dictionary containing:
        - success: Whether the analysis succeeded
        - error: Error message if success is False
        - captured_image: types.Part with raw image captured from webcam (for LLM vision)
        - annotated_image: types.Part with annotated image showing objects marked and labeled (for LLM vision)
        - center: Sky coordinates of the image center (RA/DEC)
        - field_of_view: Image dimensions in degrees and arcminutes  
        - objects: List of identified objects with:
            - name: Object designation (e.g., "M42", "VV Ori", "HIP 26311")
            - type: Category (Messier, NGC/IC, Star, Deep Sky)
            - magnitude: Visual brightness (lower = brighter)
            - spectral_type: For stars, their spectral classification
            - distance_lightyears: Distance from Earth
            - subtype: Specific object type (Galaxy, Nebula, Variable Star, etc.)
        - object_count: Total number of objects found
    
    Example result:
        {
            "success": True,
            "captured_image": <types.Part with image/png>,
            "annotated_image": <types.Part with image/png>,
            "center": {"ra_deg": 84.25, "dec_deg": -1.14, "ra_hms": "5h 37m 1s", "dec_dms": "-1° 8' 37\""},
            "field_of_view": {"width_arcmin": 110.3, "height_arcmin": 109.4},
            "objects": [
                {"name": "VV Ori", "type": "Star", "magnitude": 5.34, "subtype": "Variable Star"},
                {"name": "M42", "type": "Messier", "magnitude": 4.0, "subtype": "Nebula"},
                ...
            ],
            "object_count": 42
        }
    """
    # Call the analyze_image function which captures from webcam
    result = analyze_image(
        radius=search_radius,
        mag_limit=magnitude_limit,
        verbose=False  # Suppress logs when used as agent tool
    )
    
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
