#!/usr/bin/env python3
"""
AstroGuide - An AI-powered astronomical tour guide agent.

This agent acts as an expert astronomer providing engaging "tourist information"
about celestial objects visible through a telescope. It captures images from a webcam, uses plate solving and 
object detection, then combines this data with its knowledge and web searches to create 
fascinating narratives about what the user is seeing.
"""

from google.adk.tools.google_search_tool import GoogleSearchTool
import os
import sys
import io
from pathlib import Path

import google.genai.types as types
from google.adk.tools.function_tool import FunctionTool
from google.adk.tools.tool_context import ToolContext

# Add project root to path so we can import from src
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from google.adk.agents import Agent
from src.tools.capture_sky.tool import SkyCaptureTool
# from src.tools.search.ddg_tool import web_search

async def capture_sky(tool_context: ToolContext, image_artifact_name: str) -> dict:
    """
    Captures an image from the telescope camera and identifies stars and point sources.
    
    This tool captures a live image, performs plate solving to determine coordinates, 
    and queries catalogs to identify specific STARS and POINT SOURCES.
    
    This tool DOES NOT automatically detect nebulae, galaxies, or diffuse structures. 
    It only provides a list of stars. You MUST analyze the returned `annotated_image` artifact 
    visually to identify and describe large deep-sky objects or other bigger structures.
    
    Args:
        image_artifact_name: The name of the image artifact file to analyze.

    Returns:
        A dictionary containing:
        - success: Whether the capture succeeded
        - error: Error message if success is False
        - annotated_image_artifact: Name of the artifact containing the annotated image
        - plate_solving: Sky coordinates of the image center (RA/DEC), field of view, pixel scale
        - objects: Dictionary with:
            - identified_count: Number of objects identified via SIMBAD (mostly stars)
            - identified: List of identified objects.
    """
    try:
        # Call the capture_sky function using file path method
        sky_result = SkyCaptureTool().capture_sky_from_file(image_path=image_artifact_name)
        
        # Load and save the annotated image as an artifact
        logs_dir = sky_result.get("logs_dir")
        if logs_dir:
            annotated_path = os.path.join(logs_dir, "annotated.png")
            if os.path.exists(annotated_path):
                try:
                    with open(annotated_path, "rb") as f:
                        annotated_data = f.read()
                    
                    # Save as artifact - this stores the image efficiently
                    artifact_name = "annotated_sky_capture.png"
                    await tool_context.save_artifact(
                        filename=artifact_name,
                        artifact=types.Part.from_bytes(
                            data=annotated_data,
                            mime_type="image/png"
                        )
                    )
                    sky_result["annotated_image_artifact"] = artifact_name
                except Exception as e:
                    sky_result["annotated_image_error"] = f"Failed to save annotated image artifact: {str(e)}"
        
        # Remove logs_dir from result (internal detail)
        if "logs_dir" in sky_result:
            del sky_result["logs_dir"]
        
        return sky_result
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }

capture_sky_tool = FunctionTool(func=capture_sky)
# search_tool = FunctionTool(func=web_search)
search_tool = GoogleSearchTool(bypass_multi_tools_limit=True)

# Read the only prompt from the markdown file
import re

with open("./agents/astro_guide/prompt.md", "r") as f:
    prompt =  f.read()
    prompt = re.sub(r"<!--.*?-->", "", prompt, flags=re.DOTALL)

# Define the root agent
root_agent = Agent(
    model="gemini-3-pro-preview",
    name="astro_guide",
    description="Un astrónomo experto y guía turístico del cielo que captura imágenes del telescopio y brinda narrativas fascinantes sobre los objetos celestes.",
    instruction=prompt,
    tools=[
        capture_sky_tool,
        search_tool,
    ],
)
