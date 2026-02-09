from abc import ABC, abstractmethod
from typing import Optional
from PIL import Image as PILImage
from astropy.io.fits import Header

class PlateSolver(ABC):
    """
    Abstract interface for plate solving services.
    """
    
    @abstractmethod
    def solve(self, image: PILImage.Image) -> Header:
        """
        Perform plate solving on the given image.
        
        Args:
            image: The image to be solved.
            
        Returns:
            The WCS header information.
            
        Raises:
            RuntimeError: If plate solving fails.
        """
        pass
        
    @property
    @abstractmethod
    def name(self) -> str:
        """Return a human-readable name for this solver."""
        pass
