"""
Astronomical Image Analysis Tool - Detection-First Approach

This tool captures an image from a webcam, performs plate solving to obtain
WCS coordinates, detects celestial objects directly in the image, and then
queries SIMBAD to identify each detected object.

The detection-first approach detects objects in the image first, then queries
catalogs only for those specific positions, reducing false positives and
false negatives compared to region-based catalog queries.
"""


import base64
from datetime import datetime
import io
import os
import tempfile
import json
import pickle
import cv2
from typing import List, Optional, Tuple

import requests
from astropy.io.fits import Header
from astropy.wcs import WCS
from PIL import Image as PILImage, ImageDraw, ImageFont

from src.config import get_config_from_env
from src.utils import ra_to_hms, dec_to_dms
from src.tools.capture_sky.types import DetectedObject, CelestialObject, CelestialPosition
from src.tools.capture_sky.object_detector.contrast_detector import ContrastObjectDetector
from src.tools.capture_sky.simbad_query import query_simbad_batch


class SkyCaptureTool:
    def __init__(self):
        self.config = get_config_from_env()

    def log(self, msg: str):
        if self.config.verbose:
            print(msg)

    # =============================================================================
    # Webcam capture
    # =============================================================================

    def _capture_from_webcam(self) -> PILImage.Image:
        """
        Capture a single frame from the webcam.
        
        Raises:
            RuntimeError: If camera cannot be opened or frame cannot be captured
        """
        camera_index = self.config.webcam_index

        cap = cv2.VideoCapture(camera_index)
        if not cap.isOpened():
            raise RuntimeError(f"Could not open camera at index {camera_index}")
        
        try:
            self.log("Capturing frame...")
            
            ret, frame = cap.read()
            if not ret or frame is None:
                raise RuntimeError(f"Failed to capture frame from camera at index {camera_index}")
            
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image = PILImage.fromarray(frame_rgb)
            
            return image
            
        finally:
            cap.release()

    
    # =============================================================================
    # Plate solving and object identification
    # =============================================================================

    def _plate_solve(self, image: PILImage.Image):
        """
        Perform plate solving on an image using Astrometry.net.
        
        Returns:
            WCS header
            
        Raises:
            RuntimeError: If plate solving fails
        """
        cache_path = os.path.join(self.config.storage_dir, "logs", "wcs.pkl")
        
        # Try to load from cache if enabled
        if self.config.plate_solving_use_cache and os.path.exists(cache_path):
            try:
                self.log(f"Loading WCS from cache: {cache_path}")
                with open(cache_path, "rb") as f:
                    wcs_header = pickle.load(f)
                self.log("Successfully loaded WCS from cache")
                return wcs_header
            except Exception as e:
                self.log(f"Failed to load WCS from cache: {e}, proceeding with plate solving")
        
        # Perform plate solving
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            image.save(tmp, format='PNG')
            tmp_path = tmp.name
        
        try:
            self.log(f"Sending image to Astrometry server...")
            
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
                
                # Save to cache
                try:
                    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
                    with open(cache_path, "wb") as f:
                        pickle.dump(wcs_header, f)
                    self.log(f"Saved WCS to cache: {cache_path}")
                except Exception as e:
                    self.log(f"Failed to save WCS to cache: {e}")
                
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


    def _get_pixel_scale_arcsec(self, wcs_header) -> Optional[float]:
        """Get pixel scale in arcseconds per pixel."""
        if 'CD1_1' in wcs_header:
            return abs(wcs_header['CD1_1']) * 3600
        elif 'CDELT1' in wcs_header:
            return abs(wcs_header['CDELT1']) * 3600
        return None


    def _identify_objects(self, detected_objects: List[DetectedObject], wcs_header) -> List[Optional[CelestialObject]]:
        """
        Identify objects in the image via SIMBAD.
        
        Returns:
            List of identified CelestialObject instances
        """
        wcs = WCS(wcs_header)
        pixel_scale = self._get_pixel_scale_arcsec(wcs_header) or 1.0
        
        # Step 1: Detect objects in the image
        
        max_query_objects = self.config.max_query_objects
        if len(detected_objects) > max_query_objects:
            self.log(f"  Limiting to first {max_query_objects} detections")
            detected_objects.sort(key=lambda obj: obj.brightness, reverse=True)
            detected_objects = detected_objects[:max_query_objects]
        
        # Step 2: Convert to celestial coordinates

        self.log(f"Converting {len(detected_objects)} positions to celestial coordinates...")
        celestial_positions = []
        
        for detected_object in detected_objects:
            try:
                sky = wcs.pixel_to_world(detected_object.position.pixel_x, detected_object.position.pixel_y)
                celestial_positions.append(
                    CelestialPosition(ra=sky.ra.deg, dec=sky.dec.deg, radius_arcsec=detected_object.position.radius_px * pixel_scale) # type: ignore
                )
            except Exception as e:
                raise RuntimeError(
                    f"Failed to convert pixel position ({detected_object.position.pixel_x}, {detected_object.position.pixel_y}) "
                    f"to celestial coordinates: {e}"
                ) from e
        
        # Step 3: Query SIMBAD in parallel for all positions

        self.log(f"Querying SIMBAD for {len(celestial_positions)} positions in parallel...")
        
        identified_objects = query_simbad_batch(
            self.config,
            celestial_positions, 
            max_workers=10,
            show_progress=True,
        )
        
        self.log(f"Identified {len(identified_objects)} objects")

        return identified_objects


    # =============================================================================
    # Image annotation
    # =============================================================================

    def _annotate_image(self, image: PILImage.Image, detected_objects: List[DetectedObject], celestial_objects: List[Optional[CelestialObject]]) -> PILImage.Image:
        """
        Annotate the image with identified and unidentified objects.
        """
        img = image.convert('RGB').copy()
        draw = ImageDraw.Draw(img)
        
        # Try to load fonts
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
            font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 10)
        except:
            try:
                font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 14)
                font_small = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 10)
            except:
                font = ImageFont.load_default()
                font_small = font
        
        img_width, img_height = img.size
        
        # Color scheme
        colors = {
            'Messier': (255, 100, 100),
            'NGC/IC': (100, 255, 100),
            'Star': (100, 200, 255),
            'Deep Sky': (255, 200, 100),
            'default': (255, 255, 100),
            'unidentified': (128, 128, 128)
        }
        
        # Draw identified objects
        for (detected_object, identified_object) in zip(detected_objects, celestial_objects):
            if identified_object is None:
                continue

            try:
                x, y = detected_object.position.pixel_x, detected_object.position.pixel_y
                
                if not (0 <= x < img_width and 0 <= y < img_height):
                    continue
                
                color = colors.get(identified_object.catalog, colors['default'])
                
                radius = 15
                draw.ellipse(
                    [(x - radius, y - radius), (x + radius, y + radius)],
                    outline=color, width=2
                )
                
                label = identified_object.name
                if identified_object.magnitude_visual is not None:
                    label += f" ({identified_object.magnitude_visual:.1f})"
                
                label_x, label_y = x + radius + 5, y - 7
                bbox = draw.textbbox((label_x, label_y), label, font=font_small)
                draw.rectangle(
                    [bbox[0] - 2, bbox[1] - 1, bbox[2] + 2, bbox[3] + 1],
                    fill=(0, 0, 0, 180)
                )
                draw.text((label_x, label_y), label, fill=color, font=font_small)
                
            except Exception as e:
                raise RuntimeError(f"Failed to annotate object '{identified_object.name}' at ({detected_object.position.pixel_x}, {detected_object.position.pixel_y}): {e}") from e
        
        # Add legend
        legend_y = 10
        draw.rectangle([5, 5, 200, 115], fill=(0, 0, 0, 200), outline=(255, 255, 255))
        draw.text((10, legend_y), "Legend (v2 - Detection):", fill=(255, 255, 255), font=font)
        legend_y += 18
        for catalog, color in colors.items():
            if catalog not in ['default', 'unidentified']:
                draw.text((10, legend_y), f"● {catalog}", fill=color, font=font_small)
                legend_y += 15
        
        self.log(f"Annotated {len(celestial_objects)} identified objects")
        return img


    # =============================================================================
    # Main function
    # =============================================================================

    def capture_sky_from_file(self, image_path: str) -> dict:
        """
        Analyze a night sky image from a file path.
        
        Convenience method that reads the file and calls capture_sky with base64 encoding.
        
        Args:
            image_path: Path to the image file
        
        Returns:
            Same as capture_sky()
        """
        try:
            with open(image_path, "rb") as f:
                image_data = f.read()
            base64_image = base64.b64encode(image_data).decode("utf-8")
            return self.capture_sky(base64_image)
        except Exception as e:
            raise RuntimeError(f"Failed to read image from {image_path}: {e}")

    def capture_sky(self, base64_image: str) -> dict:
        """
        Analyze a night sky image using detection-first approach.
        
        This tool detects objects directly in the image first, then queries
        SIMBAD only at those specific positions. This reduces false positives
        (annotations for invisible objects) and false negatives (missing visible objects).
        
        Args:
            base64_image: Base64-encoded image string
        
        Returns:
            dict with:
            - success: bool
            - plate_solving: dict with center coordinates and pixel scale
            - identified_objects: List of identified celestial objects with pixel coords
        """

        # Step 0: Prepare logs dir with datetime string

        datetime_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        logs_dir = os.path.join(self.config.storage_dir, "logs", datetime_str)
        os.makedirs(logs_dir, exist_ok=True)
 
        # Step 1: Decode base64 image
        self.log(f"\n> Step 1: Decoding base64 image...")

        try:
            image_data = base64.b64decode(base64_image)
            image = PILImage.open(io.BytesIO(image_data))
        except Exception as e:
            raise RuntimeError(f"Failed to decode base64 image: {e}")
        
        captured_image = image.copy()
        captured_debug_path = os.path.join(logs_dir, "captured.png")
        captured_image.save(captured_debug_path)
        
        # Step 2: Plate solve

        self.log("\n> Step 2: Plate solving...")

        wcs_header = self._plate_solve(image)
        
        if 'CRVAL1' not in wcs_header or 'CRVAL2' not in wcs_header:
            raise Exception("Could not extract center coordinates from WCS header.")
        
        ra = float(wcs_header['CRVAL1']) # type: ignore
        dec = float(wcs_header['CRVAL2']) # type: ignore
        pixel_scale_arcsec = self._get_pixel_scale_arcsec(wcs_header)

        self.log(f"Center coordinates: RA={ra_to_hms(ra)}, DEC={dec_to_dms(dec)}, Pixel Scale={pixel_scale_arcsec}")
        
        # Step 3: Detect objects

        self.log("\n> Step 3: Detecting objects...")

        if self.config.object_detector == "contrast_detector":
            object_detector = ContrastObjectDetector()
        else:
            raise ValueError(f"Invalid object detector specified: '{self.config.object_detector}'. Supported: 'contrast_detector'")

        detected_objects = object_detector.detect(image)
        self.log(f"  Found {len(detected_objects)} objects in image using {self.config.object_detector}")

        # Step 4: Identify objects

        self.log("\n> Step 4: Identifying objects...")

        celestial_objects = self._identify_objects(detected_objects, wcs_header)
        
        # Step 5: Annotate image

        self.log("\n> Step 5: Annotating image...")

        annotated_image = self._annotate_image(image, detected_objects, celestial_objects)

        try:
            annotated_path = os.path.join(logs_dir, "annotated.png")
            annotated_image.save(annotated_path)
        except Exception as e:
            self.log(f"Failed to save annotated image: {e}")

        # Step 6: Build result
        
        self.log("\n> Step 6: Building result...")

        identified_objects = []
        for detected_obj, celestial_object in zip(detected_objects, celestial_objects):
            if celestial_object is None:
                continue
            
            # Build object dict with required fields
            obj_dict = {
                "name": celestial_object.name,
                "type": celestial_object.catalog,
                "subtype": celestial_object.object_type_description,
                "celestial_coords": {
                    "ra_deg": round(celestial_object.position.ra, 6),
                    "dec_deg": round(celestial_object.position.dec, 6),
                    "radius_arcsec": round(celestial_object.position.radius_arcsec, 2),
                },
                "pixel_coords": {
                    "x": round(detected_obj.position.pixel_x, 2),
                    "y": round(detected_obj.position.pixel_y, 2),
                    "radius_pixels": round(detected_obj.position.radius_px, 2),
                },
            }
            
            # Add optional fields only if not None
            if celestial_object.alternative_names is not None:
                obj_dict["alternative_names"] = celestial_object.alternative_names
            if celestial_object.magnitude_visual is not None:
                obj_dict["magnitude_visual"] = round(celestial_object.magnitude_visual, 2)
            if celestial_object.bv_color_index is not None:
                obj_dict["bv_color_index"] = round(celestial_object.bv_color_index, 2)
            if celestial_object.spectral_type is not None:
                obj_dict["spectral_type"] = celestial_object.spectral_type
            if celestial_object.morphological_type is not None and celestial_object.morphological_type != '':
                obj_dict["morphological_type"] = celestial_object.morphological_type
            if celestial_object.distance_lightyears is not None:
                obj_dict["distance_lightyears"] = celestial_object.distance_lightyears
            
            identified_objects.append(obj_dict)

        result = {
            "success": True,
            "plate_solving": {
                "center_ra_deg": round(ra, 6),
                "center_dec_deg": round(dec, 6),
                "pixel_scale_arcsec": round(pixel_scale_arcsec, 4) if pixel_scale_arcsec else None,
            },
            "identified_objects": identified_objects,
            "logs_dir": logs_dir,
        }
        
        try:
            json_path = os.path.join(logs_dir, "analysis.json")
            with open(json_path, "w") as f:
                json.dump(result, f, indent=2)
        except Exception as e:
            raise RuntimeError(f"Failed to save JSON: {e}") from e

        self.log("\nProcessing completed successfully.")
        
        return result
