import json
import tempfile
import os
import requests
import pickle
from typing import Optional
from PIL import Image as PILImage
from astropy.io.fits import Header
from src.config import AppConfig
from src.tools.capture_sky.plate_solver.plate_solver_interface import PlateSolver

class CustomRemotePlateSolver(PlateSolver):
    """
    Plate solver that uses a custom remote HTTP API.
    """
    
    def __init__(self, config: AppConfig):
        self.config = config

    @property
    def name(self) -> str:
        return "CustomRemoteServer"

    def solve(self, image: PILImage.Image) -> Header:
        """
        Perform plate solving using the custom remote server.
        """
        # Perform plate solving
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            image.save(tmp, format='PNG')
            tmp_path = tmp.name
        
        try:
            # Use self-hosted astrometry server
            url = self.config.astrometry_api_url
            
            with open(tmp_path, 'rb') as f:
                response = requests.post(url, files={'image': f})
                
            if response.status_code != 200:
                raise RuntimeError(f"Astrometry server returned status {response.status_code}: {response.text}")
            
            try:
                result = response.json()
            except json.JSONDecodeError:
                raise RuntimeError(f"Invalid JSON response from server: {response.text}")
            
            if result.get("status") == "success":
                wcs_content = result.get("wcs")
                if not wcs_content:
                    raise RuntimeError("Server returned success but no WCS content")
                
                # Parse WCS header from string
                wcs_header = Header.fromstring(wcs_content)
                
                return wcs_header
            else:
                msg = result.get("message", "Unknown error")
                raise RuntimeError(f"Plate solving failed: {msg}")
                
        except RuntimeError:
            raise  # Re-raise our own exceptions
        except Exception as e:
            raise RuntimeError(f"Error during plate solving: {e}") from e
        finally:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass
