from dataclasses import dataclass, asdict
from typing import Optional, List, Dict, Any


@dataclass
class ImagePosition:
    """Represents a position in image coordinates (pixels) with size (pixels)."""
    pixel_x: float
    pixel_y: float
    radius_px: float


@dataclass
class DetectedObject:
    """
    Represents a celestial object detected in an image.
    
    Attributes:
        position: Position of the object centroid in pixels
        radius_px: Approximate size/radius of the object in pixels
        brightness: Relative brightness score (higher = brighter)
        area_px: Area of the detected region in pixels (for diffuse objects)
        is_point_source: Whether this appears to be a point source (star) vs extended object
    """
    position: ImagePosition
    brightness: float
    area_px: Optional[float] = None
    is_point_source: bool = True


@dataclass
class CelestialPosition:
    """Represents a position in celestial coordinates (degrees) with size (arcseconds)."""
    ra: float
    dec: float
    radius_arcsec: float

@dataclass
class CelestialObject:
    """Represents a detected and identified celestial object."""
    # Core identification
    name: str
    catalog: str  # 'Messier', 'NGC/IC', 'Star', 'Deep Sky'
    
    # Celestial coordinates (required)
    position: CelestialPosition
    
    # Optional identification
    alternative_names: Optional[List[str]] = None
    object_type_description: Optional[str] = None
    
    # Optional astronomical properties
    magnitude_visual: Optional[float] = None
    bv_color_index: Optional[float] = None
    spectral_type: Optional[str] = None
    morphological_type: Optional[str] = None
    distance_lightyears: Optional[float] = None
