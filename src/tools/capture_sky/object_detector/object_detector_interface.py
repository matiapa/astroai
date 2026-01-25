"""
Abstract interface for celestial object detection in astronomical images.

This module defines the interface that all celestial object detectors must implement,
allowing different detection algorithms to be swapped without changing the rest of the pipeline.
"""

from abc import ABC, abstractmethod
from typing import List
from PIL import Image as PILImage

from src.tools.capture_sky.types import DetectedObject


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
