import os
import tempfile
from PIL import Image as PILImage
from astropy.io.fits import Header
from astroquery.astrometry_net import AstrometryNet
from src.config import AppConfig
from src.tools.capture_sky.plate_solver.plate_solver_interface import PlateSolver

class AstrometryNetPlateSolver(PlateSolver):
    """
    Plate solver that uses the official Astrometry.net service via the astrometry package.
    """
    
    def __init__(self, config: AppConfig):
        self.config = config
        self.ast = AstrometryNet()
        self.ast.api_key = self.config.astrometry_api_key

    @property
    def name(self) -> str:
        return "Astrometry.net"

    def solve(self, image: PILImage.Image) -> Header:
        """
        Perform plate solving using Astrometry.net.
        """
        if not self.config.astrometry_api_key:
             raise ValueError("ASTROMETRY_API_KEY is required for Astrometry.net solver")

        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            image.save(tmp, format='PNG')
            tmp_path = tmp.name

        try:
             # Timeout is in seconds
            wcs_header = self.ast.solve_from_image(
                tmp_path, 
                solve_timeout=self.config.plate_solving_timeout,
                force_image_upload=True
            )
            
            if wcs_header:
                return wcs_header
            else:
                 raise RuntimeError("Astrometry.net failed to solve the image (no WCS returned).")

        except Exception as e:
            raise RuntimeError(f"Error during Astrometry.net plate solving: {e}") from e
        finally:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass
