"""
DTOs for the /analyze endpoint.
"""

from typing import Optional, List
from pydantic import BaseModel


class CelestialCoords(BaseModel):
    """Celestial coordinates."""
    ra_deg: float
    dec_deg: float
    radius_arcsec: float


class PixelCoords(BaseModel):
    """Pixel coordinates."""
    x: float
    y: float
    radius_pixels: float


class IdentifiedObject(BaseModel):
    """Identified celestial object."""
    name: str
    type: str
    subtype: Optional[str] = None
    magnitude_visual: Optional[float] = None
    bv_color_index: Optional[float] = None
    spectral_type: Optional[str] = None
    morphological_type: Optional[str] = None
    distance_lightyears: Optional[float] = None
    alternative_names: Optional[List[str]] = None
    celestial_coords: CelestialCoords
    pixel_coords: PixelCoords
    legend: Optional[str] = None


class PlateSolving(BaseModel):
    """Plate solving results."""
    center_ra_deg: float
    center_dec_deg: float
    pixel_scale_arcsec: Optional[float] = None


class Narration(BaseModel):
    """Narration data."""
    title: str
    text: str
    audio_url: str


class AnalyzeResponse(BaseModel):
    """Response body for /analyze endpoint."""
    success: bool
    plate_solving: Optional[PlateSolving] = None
    narration: Optional[Narration] = None
    identified_objects: Optional[List[IdentifiedObject]] = None
    error: Optional[str] = None
