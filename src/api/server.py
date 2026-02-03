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

from src.api.analyze.dto import AnalyzeResponse
from src.api.analyze.controller import analyze_image, TMP_DIR


# ============================================================================
# FastAPI Application
# ============================================================================

app = FastAPI(
    title="AstroIA API",
    description="Astronomical image analysis API with AI-powered narration",
    version="1.0.0"
)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "ok", "service": "AstroIA API"}


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze(
    req: Request,
    image: UploadFile = File(..., description="Astronomical image file"),
    language: str = Form(default="es", description="ISO language code for narration")
) -> AnalyzeResponse:
    """
    Analyze an astronomical image.
    
    Receives an image file and optional language code via multipart form,
    performs plate solving and object detection,
    generates narration using Gemini AI, and returns audio via Gemini TTS.
    """
    base_url = str(req.base_url).rstrip("/")
    return await analyze_image(image, language, base_url)


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
        filename=filename
    )


def main():
    """Run the API server."""
    host = os.environ.get("API_HOST", "0.0.0.0")
    port = int(os.environ.get("API_PORT", "8000"))
    
    print(f"Starting AstroIA API server on {host}:{port}")
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
