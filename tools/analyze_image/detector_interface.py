"""
Abstract interface for celestial object detection in astronomical images.

This module defines the interface that all celestial object detectors must implement,
allowing different detection algorithms to be swapped without changing the rest of the pipeline.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional
from PIL import Image as PILImage


@dataclass
class DetectedObject:
    """
    Represents a celestial object detected in an image.
    
    Attributes:
        x: X-coordinate of the object centroid in pixels
        y: Y-coordinate of the object centroid in pixels
        radius_px: Approximate size/radius of the object in pixels
        brightness: Relative brightness score (higher = brighter)
        area_px: Area of the detected region in pixels (for diffuse objects)
        is_point_source: Whether this appears to be a point source (star) vs extended object
    """
    x: float
    y: float
    radius_px: float
    brightness: float
    area_px: Optional[float] = None
    is_point_source: bool = True


class CelestialObjectDetector(ABC):
    """
    Abstract base class for celestial object detection algorithms.
    
    Implementations should detect any regions in the image that contrast
    against the celestial background, regardless of their nature (stars,
    galaxies, nebulae, clusters, etc.).
    """
    
    @abstractmethod
    def detect(self, image: PILImage.Image) -> List[DetectedObject]:
        """
        Detect celestial objects in the given image.
        
        Args:
            image: PIL Image to analyze. Can be RGB or grayscale.
        
        Returns:
            List of DetectedObject instances representing found objects,
            sorted by brightness (brightest first).
        """
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Return a human-readable name for this detector."""
        pass
