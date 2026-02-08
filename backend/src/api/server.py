"""
AstroIA API Server

FastAPI server providing the POST /analyze endpoint for astronomical image analysis.
"""

from src.config import get_config_from_env
import os
import sys
from pathlib import Path

from fastapi import FastAPI, Request, UploadFile, File, Form
from fastapi.responses import FileResponse
import uvicorn

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from sse_starlette.sse import EventSourceResponse

from src.api.analyze.dto import AnalyzeResponse
from src.api.analyze.controller import analyze_image_stream


from fastapi.middleware.cors import CORSMiddleware

from agents.astro_guide.agent import a2a_app, setup_a2a

# ============================================================================
# FastAPI Application
# ============================================================================

app = FastAPI(
    title="AstroIA API",
    description="Astronomical image analysis API with AI-powered narration",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount A2A agent as a sub-application
app.mount("/a2a", a2a_app)


@app.on_event("startup")
async def on_startup():
    """Build the A2A agent card and register routes on the mounted sub-app."""
    await setup_a2a()


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "ok", "service": "AstroIA API"}


@app.post("/analyze")
async def analyze(
    req: Request,
    image: UploadFile = File(..., description="Astronomical image file"),
    language: str = Form(default="es", description="ISO language code for narration")
):
    """
    Analyze an astronomical image.
    
    Returns an SSE stream with progress updates and final result:
    - event: analyzing_image
    - event: generating_narration
    - event: generating_audio
    - event: analysis_finished (payload is AnalyzeResponse JSON)
    """
    base_url = str(req.base_url).rstrip("/")
    return EventSourceResponse(analyze_image_stream(image, language, base_url))


@app.get("/audio/{filename}")
async def get_audio(filename: str):
    """
    Serve audio files from the audios directory.
    """
    config = get_config_from_env()
    audios_dir = os.path.join(config.storage_dir, "audios")
    
    if not os.path.exists(audios_dir):
        return {"error": "Audio file not found"}, 404
    
    return FileResponse(
        path=os.path.join(audios_dir, filename),
        media_type="audio/wav",
        filename=filename,
        headers={"Access-Control-Allow-Origin": "*"}
    )


def main():
    """Run the API server."""
    host = os.environ.get("API_HOST", "0.0.0.0")
    port = int(os.environ.get("API_PORT", "8000"))
    
    print(f"Starting AstroIA API server on {host}:{port}")
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
