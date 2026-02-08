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

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from starlette.applications import Starlette

from google.adk.a2a.executor.a2a_agent_executor import A2aAgentExecutor, A2aAgentExecutorConfig
from google.adk.a2a.converters.request_converter import convert_a2a_request_to_agent_run_request
from google.adk.agents.run_config import RunConfig, StreamingMode
from a2a.types import AgentCapabilities
from google.adk.a2a.utils.agent_card_builder import AgentCardBuilder
from google.adk.artifacts.in_memory_artifact_service import InMemoryArtifactService
from google.adk.auth.credential_service.in_memory_credential_service import InMemoryCredentialService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.adk.runners import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService

_url = os.environ.get("PUBLIC_API_URL", "http://localhost:8000")


def _streaming_aware_request_converter(context, part_converter):
    """Custom request converter that enables SSE streaming for message/stream requests."""
    run_request = convert_a2a_request_to_agent_run_request(context, part_converter)
    if (
        context.call_context
        and context.call_context.state.get("method") == "message/stream"
    ):
        run_request.run_config = RunConfig(
            streaming_mode=StreamingMode.SSE,
            custom_metadata=run_request.run_config.custom_metadata if run_request.run_config else {},
        )
    return run_request


async def _create_runner() -> Runner:
    return Runner(
        app_name=root_agent.name or "adk_agent",
        agent=root_agent,
        artifact_service=InMemoryArtifactService(),
        session_service=InMemorySessionService(),
        memory_service=InMemoryMemoryService(),
        credential_service=InMemoryCredentialService(),
    )


_task_store = InMemoryTaskStore()
_agent_executor = A2aAgentExecutor(
    runner=_create_runner,
    config=A2aAgentExecutorConfig(
        request_converter=_streaming_aware_request_converter,
    ),
)
_request_handler = DefaultRequestHandler(
    agent_executor=_agent_executor,
    task_store=_task_store,
)

# Empty Starlette app — routes are added during startup via setup_a2a()
a2a_app = Starlette()


async def setup_a2a():
    """Build the auto-generated agent card and register A2A routes.

    Must be called from the parent FastAPI app's startup event, since
    mounted sub-apps don't get their own startup events triggered.
    """
    agent_card = await AgentCardBuilder(
        agent=root_agent,
        rpc_url=f"{_url}/a2a/",
        capabilities=AgentCapabilities(streaming=True),
    ).build()

    A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=_request_handler,
    ).add_routes_to_app(a2a_app)
