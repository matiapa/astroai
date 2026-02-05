"""
AstroIA API Server

FastAPI server providing the POST /analyze endpoint for astronomical image analysis.
"""

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
from src.api.analyze.controller import analyze_image_stream, TMP_DIR


from fastapi.middleware.cors import CORSMiddleware

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
    Serve audio files from the tmp directory.
    """
    file_path = os.path.join(TMP_DIR, filename)
    
    if not os.path.exists(file_path):
        return {"error": "Audio file not found"}, 404
    
    return FileResponse(
        path=file_path,
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
