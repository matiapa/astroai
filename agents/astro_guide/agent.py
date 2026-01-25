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

import google.genai.types as types
from google.adk.tools.function_tool import FunctionTool

# Add project root to path so we can import from src
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from google.adk.agents import Agent
from google.adk.tools.google_search_tool import google_search

from src.tools.capture_sky.tool import SkyCaptureTool


def capture_sky() -> dict:
    """
    Captures an image from the telescope camera and identifies stars and point sources.
    
    This tool captures a live image, performs plate solving to determine coordinates, 
    and queries catalogs to identify specific STARS and POINT SOURCES.
    
    This tool DOES NOT automatically detect nebulae, galaxies, or diffuse structures. 
    It only provides a list of stars. You MUST analyze the returned `captured_image` visually 
    to identify and describe large deep-sky objects or other bigger structures.
    
    Returns:
        A dictionary containing:
        - success: Whether the capture succeeded
        - error: Error message if success is False
        - captured_image: types.Part with raw image captured from webcam
        - annotated_image: types.Part with annotated image (only stars are likely marked)
        - plate_solving: Sky coordinates of the image center (RA/DEC), field of view, pixel scale
        - objects: Dictionary with:
            - identified_count: Number of objects identified via SIMBAD (mostly stars)
            - identified: List of identified objects.
    """
    try:
        # Call the capture_sky function which returns a SkyCaptureResult dataclass
        sky_result = SkyCaptureTool().capture_sky()
        
        # Convert images to types.Part for proper multimodal handling
        # This allows Gemini to actually "see" the images using its vision capabilities
        for key, image in [("captured_image", sky_result["captured_image"]), ("annotated_image", sky_result["captured_image_annotated"])]:
            if image is not None:
                try:
                    buffered = io.BytesIO()
                    image.save(buffered, format="PNG")
                    # Create a types.Part with inline binary data
                    sky_result[key] = types.Part.from_bytes(
                        data=buffered.getvalue(),
                        mime_type="image/png"
                    )
                except Exception as e:
                    sky_result[key] = None
                    sky_result[f"{key}_error"] = f"Failed to encode image: {str(e)}"
        
        return sky_result
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }

capture_sky_tool = FunctionTool(func=capture_sky)

# Read the only prompt from the markdown file
with open("./agents/astro_guide/prompt.md", "r") as f:
    prompt = f.read()

# Define the root agent
root_agent = Agent(
    model="gemini-3-flash-preview",
    name="astro_guide",
    description="Un astrónomo experto y guía turístico del cielo que captura imágenes del telescopio y brinda narrativas fascinantes sobre los objetos celestes.",
    instruction=prompt,
    tools=[
        capture_sky_tool,
        # google_search,
    ],
)
