"""
Astronomical Image Analysis Tool - Detection-First Approach

This tool captures an image from a webcam, performs plate solving to obtain
WCS coordinates, detects celestial objects directly in the image, and then
queries SIMBAD to identify each detected object.

The detection-first approach detects objects in the image first, then queries
catalogs only for those specific positions, reducing false positives and
false negatives compared to region-based catalog queries.
"""

import os
import io
import tempfile
import json
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple

import cv2
from astroquery.astrometry_net import AstrometryNet
from astropy.coordinates import SkyCoord
from astropy.wcs import WCS
import astropy.units as u
import numpy as np
from PIL import Image as PILImage, ImageDraw, ImageFont
import dotenv

from .detector_interface import CelestialObjectDetector, DetectedObject
from .contrast_detector import ContrastDetector

dotenv.load_dotenv()


# =============================================================================
# Configuration from environment
# =============================================================================

def _get_config():
    """Get configuration from environment variables."""
    return {
        # Astrometry.net configuration
        "api_key": os.environ.get("ASTROMETRY_API_KEY"),
        "timeout": int(os.environ.get("ASTROMETRY_TIMEOUT", "120")),
        # Webcam configuration
        "webcam_index": int(os.environ.get("WEBCAM_INDEX", "0")),
        "webcam_width": int(os.environ.get("WEBCAM_WIDTH", "0")) or None,
        "webcam_height": int(os.environ.get("WEBCAM_HEIGHT", "0")) or None,
        "webcam_warmup_frames": int(os.environ.get("WEBCAM_WARMUP_FRAMES", "5")),
    }


def _get_debug_dir() -> str:
    """Get or create the debug output directory for this run."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    debug_dir = os.path.join(os.path.dirname(__file__), "..", "..", "tmp", "captures", timestamp)
    os.makedirs(debug_dir, exist_ok=True)
    return debug_dir


# =============================================================================
# Helper functions
# =============================================================================

def _ra_to_hms(ra_deg: float) -> str:
    """Convert RA from degrees to hours, minutes, seconds format."""
    ra_hours = ra_deg / 15.0
    h = int(ra_hours)
    m = int((ra_hours - h) * 60)
    s = ((ra_hours - h) * 60 - m) * 60
    return f"{h}h {m}m {s:.2f}s"


def _dec_to_dms(dec_deg: float) -> str:
    """Convert DEC from degrees to degrees, minutes, seconds format."""
    sign = "+" if dec_deg >= 0 else "-"
    dec_abs = abs(dec_deg)
    d = int(dec_abs)
    m = int((dec_abs - d) * 60)
    s = ((dec_abs - d) * 60 - m) * 60
    return f"{sign}{d}° {m}' {s:.2f}\""


# =============================================================================
# Webcam capture
# =============================================================================

def _capture_from_webcam(config: Dict[str, Any], log) -> Optional[PILImage.Image]:
    """
    Capture a single frame from the webcam.
    
    Works with both physical cameras (e.g., connected to a telescope) and 
    virtual cameras (e.g., OBS Virtual Camera streaming from Stellarium).
    """
    camera_index = config["webcam_index"]
    width = config["webcam_width"]
    height = config["webcam_height"]
    warmup_frames = config["webcam_warmup_frames"]
        
    cap = cv2.VideoCapture(camera_index)
    
    if not cap.isOpened():
        log(f"Error: Could not open camera at index {camera_index}")
        return None
    
    try:
        if width is not None:
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        if height is not None:
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        
        actual_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        actual_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        if warmup_frames > 0:
            log(f"Camera warmup: skipping {warmup_frames} frames...")
            for _ in range(warmup_frames):
                cap.read()
        
        log("Capturing frame...")
        ret, frame = cap.read()
        
        if not ret or frame is None:
            log("Error: Failed to capture frame from camera")
            return None
        
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = PILImage.fromarray(frame_rgb)
        
        return image
        
    finally:
        cap.release()


# =============================================================================
# Plate solving
# =============================================================================

def _plate_solve(image: PILImage.Image, api_key: str, timeout: int, log):
    """
    Perform plate solving on an image using Astrometry.net.
    
    Returns:
        WCS header if successful, None otherwise
    """
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
        image.save(tmp, format='PNG')
        tmp_path = tmp.name
    
    try:
        ast = AstrometryNet()
        ast.api_key = api_key
        
        log(f"Sending image to Astrometry.net for plate solving (timeout={timeout}s)...")
        wcs_header = ast.solve_from_image(tmp_path, solve_timeout=timeout)
        
        if wcs_header:
            return wcs_header
        else:
            log("Plate solving failed - could not solve the image")
            return None
            
    except Exception as e:
        log(f"Error during plate solving: {e}")
        return None
    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass


# =============================================================================
# FOV calculation
# =============================================================================

def _calculate_fov(wcs_header, image: PILImage.Image) -> Optional[Tuple[float, float, float]]:
    """
    Calculate the field of view from the WCS header and image dimensions.
    
    Returns:
        (fov_width, fov_height, fov_diagonal) in degrees, or None if cannot calculate
    """
    try:
        width_px, height_px = image.size
        
        if 'CD1_1' in wcs_header and 'CD2_2' in wcs_header:
            cd1_1 = wcs_header['CD1_1']
            cd1_2 = wcs_header.get('CD1_2', 0)
            cd2_1 = wcs_header.get('CD2_1', 0)
            cd2_2 = wcs_header['CD2_2']
            
            pixel_scale_x = np.sqrt(cd1_1**2 + cd2_1**2)
            pixel_scale_y = np.sqrt(cd1_2**2 + cd2_2**2)
        elif 'CDELT1' in wcs_header and 'CDELT2' in wcs_header:
            pixel_scale_x = abs(wcs_header['CDELT1'])
            pixel_scale_y = abs(wcs_header['CDELT2'])
        else:
            return None
        
        fov_width = width_px * pixel_scale_x
        fov_height = height_px * pixel_scale_y
        fov_diagonal = np.sqrt(fov_width**2 + fov_height**2)
        
        return fov_width, fov_height, fov_diagonal
    
    except Exception:
        return None


def _get_pixel_scale_arcsec(wcs_header) -> Optional[float]:
    """Get pixel scale in arcseconds per pixel."""
    if 'CD1_1' in wcs_header:
        return abs(wcs_header['CD1_1']) * 3600
    elif 'CDELT1' in wcs_header:
        return abs(wcs_header['CDELT1']) * 3600
    return None


# =============================================================================
# Pixel to celestial coordinate conversion
# =============================================================================

def _pixel_to_celestial(x: float, y: float, wcs: WCS) -> Tuple[float, float]:
    """
    Convert pixel coordinates to celestial coordinates.
    
    Args:
        x, y: Pixel coordinates
        wcs: WCS object for coordinate transformation
    
    Returns:
        (ra, dec) in degrees
    """
    sky = wcs.pixel_to_world(x, y)
    return sky.ra.deg, sky.dec.deg


# =============================================================================
# Debug visualization
# =============================================================================

def _save_detections_image(
    image: PILImage.Image,
    detected: List[DetectedObject],
    output_path: str,
    log
) -> None:
    """
    Save an image with detected object positions marked (without labels).
    This is for debugging purposes, before SIMBAD identification.
    """
    img = image.convert('RGB').copy()
    draw = ImageDraw.Draw(img)
    
    for det in detected:
        x, y = det.x, det.y
        radius = max(det.radius_px * 1.5, 8)  # Scale up slightly for visibility
        
        # Color based on brightness (brighter = more yellow, fainter = more blue)
        brightness_normalized = min(det.brightness / 255.0, 1.0)
        r = int(100 + 155 * brightness_normalized)
        g = int(200 + 55 * brightness_normalized)
        b = int(255 - 155 * brightness_normalized)
        color = (r, g, b)
        
        # Draw circle at detection position
        draw.ellipse(
            [(x - radius, y - radius), (x + radius, y + radius)],
            outline=color, width=2
        )
        
        # Draw small crosshair at center
        cross_size = 3
        draw.line([(x - cross_size, y), (x + cross_size, y)], fill=color, width=1)
        draw.line([(x, y - cross_size), (x, y + cross_size)], fill=color, width=1)
    
    img.save(output_path)
    log(f"  Debug: Saved detections image to {output_path}")


# =============================================================================
# Object detection and identification
# =============================================================================

def _detect_and_identify_objects(
    image: PILImage.Image,
    wcs_header,
    detector: CelestialObjectDetector,
    simbad_radius_arcsec: float,
    debug_dir: Optional[str],
    max_detections: Optional[int],
    log
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Detect objects in the image and identify them via SIMBAD.
    
    Returns:
        Tuple of (identified_objects, unidentified_objects)
    """
    wcs = WCS(wcs_header)
    pixel_scale = _get_pixel_scale_arcsec(wcs_header) or 1.0
    
    # Step 1: Detect objects in the image
    log(f"Detecting objects using {detector.name}...")
    detected = detector.detect(image)
    log(f"  Found {len(detected)} objects in image")
    
    # Save debug image with detections (before SIMBAD query)
    if debug_dir and detected:
        detections_path = os.path.join(debug_dir, "2_detections.png")
        _save_detections_image(image, detected, detections_path, log)
    
    if not detected:
        return [], []
    
    # Limit detections for debugging if requested
    if max_detections is not None and len(detected) > max_detections:
        log(f"  Limiting to first {max_detections} detections for debugging")
        detected = detected[:max_detections]
    
    # Step 2: Convert to celestial coordinates
    log(f"Converting {len(detected)} positions to celestial coordinates...")
    positions_with_metadata = []
    
    for det in detected:
        try:
            ra, dec = _pixel_to_celestial(det.x, det.y, wcs)
            search_radius = max(
                simbad_radius_arcsec,
                det.radius_px * pixel_scale * 0.5
            )
            positions_with_metadata.append({
                'ra': ra,
                'dec': dec,
                'search_radius': search_radius,
                'det': det
            })
        except Exception:
            continue
    
    # Step 3: Query SIMBAD in parallel for all positions
    log(f"Querying SIMBAD for {len(positions_with_metadata)} positions in parallel...")
    
    # Debug: print first few positions
    for i, p in enumerate(positions_with_metadata[:3]):
        log(f"  Position {i+1}: RA={p['ra']:.6f}°, Dec={p['dec']:.6f}°, radius={p['search_radius']:.1f}\"")
    if len(positions_with_metadata) > 3:
        log(f"  ... and {len(positions_with_metadata) - 3} more")
    
    from .simbad_query import query_simbad_batch
    
    positions = [(p['ra'], p['dec']) for p in positions_with_metadata]
    simbad_results = query_simbad_batch(
        positions, 
        radius_arcsec=simbad_radius_arcsec,
        max_workers=10,
        show_progress=True
    )
    
    # Step 4: Process results
    identified_objects = []
    unidentified_objects = []
    seen_names = set()
    
    for i, (pos_meta, simbad_result) in enumerate(zip(positions_with_metadata, simbad_results)):
        det = pos_meta['det']
        
        if simbad_result:
            name = simbad_result['name']
            
            # Skip duplicates (same object detected multiple times)
            if name in seen_names:
                continue
            seen_names.add(name)
            
            # Add detection metadata
            simbad_result['pixel_x'] = det.x
            simbad_result['pixel_y'] = det.y
            simbad_result['detection_brightness'] = det.brightness
            simbad_result['is_point_source'] = det.is_point_source
            
            identified_objects.append(simbad_result)
        else:
            # Object visible but not identified in SIMBAD
            unidentified_objects.append({
                'pixel_x': det.x,
                'pixel_y': det.y,
                'ra': pos_meta['ra'],
                'dec': pos_meta['dec'],
                'brightness': det.brightness,
                'radius_px': det.radius_px,
                'is_point_source': det.is_point_source
            })
    
    log(f"Identified {len(identified_objects)} objects, {len(unidentified_objects)} unidentified")
    return identified_objects, unidentified_objects


# =============================================================================
# Image annotation
# =============================================================================

def _annotate_image(
    image: PILImage.Image,
    identified_objects: List[Dict],
    unidentified_objects: List[Dict],
    log
) -> PILImage.Image:
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
    for obj in identified_objects:
        try:
            x, y = obj.get('pixel_x', 0), obj.get('pixel_y', 0)
            
            if not (0 <= x < img_width and 0 <= y < img_height):
                continue
            
            color = colors.get(obj.get('catalog', 'default'), colors['default'])
            
            radius = 15
            draw.ellipse(
                [(x - radius, y - radius), (x + radius, y + radius)],
                outline=color, width=2
            )
            
            label = obj['name']
            if obj.get('mag') is not None:
                label += f" ({obj['mag']:.1f})"
            
            label_x, label_y = x + radius + 5, y - 7
            bbox = draw.textbbox((label_x, label_y), label, font=font_small)
            draw.rectangle(
                [bbox[0] - 2, bbox[1] - 1, bbox[2] + 2, bbox[3] + 1],
                fill=(0, 0, 0, 180)
            )
            draw.text((label_x, label_y), label, fill=color, font=font_small)
            
        except Exception:
            continue
    
    # Optionally draw unidentified objects (smaller, gray markers)
    for obj in unidentified_objects[:20]:  # Limit to avoid clutter
        try:
            x, y = obj.get('pixel_x', 0), obj.get('pixel_y', 0)
            
            if not (0 <= x < img_width and 0 <= y < img_height):
                continue
            
            color = colors['unidentified']
            radius = 8
            draw.ellipse(
                [(x - radius, y - radius), (x + radius, y + radius)],
                outline=color, width=1
            )
        except Exception:
            continue
    
    # Add legend
    legend_y = 10
    draw.rectangle([5, 5, 200, 115], fill=(0, 0, 0, 200), outline=(255, 255, 255))
    draw.text((10, legend_y), "Legend (v2 - Detection):", fill=(255, 255, 255), font=font)
    legend_y += 18
    for catalog, color in colors.items():
        if catalog not in ['default', 'unidentified']:
            draw.text((10, legend_y), f"● {catalog}", fill=color, font=font_small)
            legend_y += 15
    draw.text((10, legend_y), f"○ Unidentified", fill=colors['unidentified'], font=font_small)
    
    log(f"Annotated {len(identified_objects)} identified + {min(len(unidentified_objects), 20)} unidentified objects")
    return img


# =============================================================================
# Main API function
# =============================================================================

def analyze_image(
    detector: Optional[CelestialObjectDetector] = None,
    simbad_radius_arcsec: float = 10.0,
    max_detections: Optional[int] = None,
    verbose: bool = False
) -> Dict[str, Any]:
    """
    Capture an image from webcam and analyze it using detection-first approach.
    
    This tool detects objects directly in the image first, then queries
    SIMBAD only at those specific positions. This reduces false positives
    (annotations for invisible objects) and false negatives (missing visible objects).
    
    Args:
        detector: CelestialObjectDetector implementation to use.
                  If None, uses ContrastDetector with default settings.
        simbad_radius_arcsec: Search radius (arcseconds) for SIMBAD queries
                              at each detected position. Default: 10"
        max_detections: Maximum number of detected objects to process.
                        Useful for debugging. Default: None (process all)
        verbose: Whether to print progress messages. Default: False
    
    Returns:
        A dictionary containing:
        - success: bool - Whether the analysis succeeded
        - error: str - Error message if success is False
        - captured_image: PIL.Image - The raw captured image from webcam
        - annotated_image: PIL.Image - The image with objects marked
        - plate_solving: dict - Center coordinates, FOV, and pixel scale
        - objects: dict - Detected and identified celestial objects
    
    Configuration (via environment variables):
        ASTROMETRY_API_KEY: API key for Astrometry.net (required)
        ASTROMETRY_TIMEOUT: Timeout in seconds for plate solving (default: 120)
        
        WEBCAM_INDEX: Camera device index (default: 0)
        WEBCAM_WIDTH: Capture width in pixels (default: camera native)
        WEBCAM_HEIGHT: Capture height in pixels (default: camera native)
        WEBCAM_WARMUP_FRAMES: Frames to skip for warmup (default: 5)
    
    Example:
        >>> from analyze_image_tool_v2 import analyze_image_v2
        >>> 
        >>> # Use default contrast detector
        >>> result = analyze_image_v2(verbose=True)
        >>> 
        >>> if result["success"]:
        ...     print(f"Found {result['objects']['identified_count']} objects")
        ...     for obj in result['objects']['identified']:
        ...         print(f"  - {obj['name']}")
        ... else:
        ...     print(f"Error: {result['error']}")
    """
    def log(msg: str):
        if verbose:
            print(msg)
    
    config = _get_config()
    
    # Validate API key
    if not config["api_key"]:
        return {
            "success": False,
            "error": "ASTROMETRY_API_KEY environment variable is required."
        }
    
    # Use default detector if not provided
    if detector is None:
        detector = ContrastDetector()
    
    # Create debug directory for this run
    debug_dir = _get_debug_dir()
    log(f"Debug output directory: {debug_dir}")
    
    # Step 1: Capture from webcam
    log("\n> Step 1: Capturing image from webcam...")
    image = _capture_from_webcam(config, log)
    
    if image is None:
        return {
            "success": False,
            "error": f"Failed to capture image from webcam at index {config['webcam_index']}."
        }
    
    captured_image = image.copy()
    
    # Save captured image immediately for debugging
    captured_debug_path = os.path.join(debug_dir, "1_captured.png")
    captured_image.save(captured_debug_path)
    log(f"  Debug: Saved captured image to {captured_debug_path}")
    
    # Step 2: Plate solve
    log("\n> Step 2: Plate solving...")
    wcs_header = _plate_solve(
        image, 
        config["api_key"], 
        config["timeout"], 
        log
    )
    
    if wcs_header is None:
        return {
            "success": False,
            "error": "Plate solving failed. The image could not be matched to any known star field."
        }
    
    # Extract center coordinates
    if 'CRVAL1' not in wcs_header or 'CRVAL2' not in wcs_header:
        return {
            "success": False,
            "error": "Could not extract center coordinates from WCS header."
        }
    
    ra = float(wcs_header['CRVAL1'])
    dec = float(wcs_header['CRVAL2'])
    
    log(f"Center coordinates: RA={_ra_to_hms(ra)}, DEC={_dec_to_dms(dec)}")
    
    # Calculate FOV
    fov_info = _calculate_fov(wcs_header, image)
    fov_width, fov_height, fov_diagonal = (None, None, None)
    
    if fov_info:
        fov_width, fov_height, fov_diagonal = fov_info
        log(f"Field of view: {fov_width*60:.1f}' x {fov_height*60:.1f}'")
    
    pixel_scale_arcsec = _get_pixel_scale_arcsec(wcs_header)
    
    # Step 3: Detect and identify objects
    log("\n> Step 3: Detecting celestial objects in image...")
    identified, unidentified = _detect_and_identify_objects(
        image,
        wcs_header,
        detector,
        simbad_radius_arcsec,
        debug_dir,
        max_detections,
        log
    )
    
    # Step 4: Annotate image
    log("\n> Step 4: Annotating image...")
    annotated_image = _annotate_image(image, identified, unidentified, log)
    
    # Build output objects list
    objects_for_output = []
    for obj in identified:
        obj_data = {
            "name": obj['name'],
            "type": obj.get('catalog', 'Unknown'),
        }
        
        # Add subtype only if it's not just "Star" (that's already implied by catalog)
        subtype = obj.get('object_type_description', '')
        if subtype and subtype != 'Star':
            obj_data["subtype"] = subtype
        
        if obj.get('mag') is not None:
            obj_data["magnitude_v"] = round(obj['mag'], 2)
        if obj.get('bv_color_index') is not None:
            obj_data["bv_color_index"] = obj['bv_color_index']
        if obj.get('spectral_type'):
            obj_data["spectral_type"] = obj['spectral_type']
        if obj.get('morphological_type'):
            obj_data["morphological_type"] = obj['morphological_type']
        if obj.get('distance_lightyears'):
            obj_data["distance_lightyears"] = round(obj['distance_lightyears'], 1)
        
        objects_for_output.append(obj_data)
    
    # Build FOV data
    fov_data = None
    if fov_width is not None:
        fov_data = {
            "width_arcmin": round(fov_width * 60, 2),
            "height_arcmin": round(fov_height * 60, 2),
            "diagonal_arcmin": round(fov_diagonal * 60, 2)
        }
    
    # Save final results to debug directory
    try:
        annotated_path = os.path.join(debug_dir, "3_annotated.png")
        annotated_image.save(annotated_path)
        
        output_json = {
            "plate_solving": {
                "center": {
                    "ra_deg": round(ra, 6),
                    "dec_deg": round(dec, 6),
                },
                "pixel_scale_arcsec": round(pixel_scale_arcsec, 4) if pixel_scale_arcsec else None,
                "field_of_view": fov_data
            },
            "objects": {
                "count": len(objects_for_output),
                "items": objects_for_output
            }
        }
        
        json_path = os.path.join(debug_dir, "analysis.json")
        with open(json_path, "w") as f:
            json.dump(output_json, f, indent=2)
            
        log(f"\nResults saved to: {debug_dir}")
            
    except Exception as e:
        log(f"Failed to save capture results: {e}")
    
    return {
        "success": True,
        "captured_image": captured_image,
        "annotated_image": annotated_image,
        "plate_solving": {
            "center": {
                "ra_deg": round(ra, 6),
                "dec_deg": round(dec, 6),
                "ra_hms": _ra_to_hms(ra),
                "dec_dms": _dec_to_dms(dec)
            },
            "pixel_scale_arcsec": round(pixel_scale_arcsec, 4) if pixel_scale_arcsec else None,
            "field_of_view": fov_data
        },"objects": {
            "identified_count": len(objects_for_output),
            "identified": objects_for_output,
            "unidentified_count": len(unidentified),
            "unidentified": [
                {
                    "ra": obj['ra'],
                    "dec": obj['dec'],
                    "brightness": obj['brightness']
                }
                for obj in unidentified[:50]  # Limit unidentified in output
            ]
        }
    }
