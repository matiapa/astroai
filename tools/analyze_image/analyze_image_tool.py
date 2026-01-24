import os
import io
import tempfile
import json
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple

import cv2
from astroquery.astrometry_net import AstrometryNet
from astroquery.vizier import Vizier
from astroquery.simbad import Simbad
from astropy.coordinates import SkyCoord
from astropy.wcs import WCS
import astropy.units as u
from astropy.stats import sigma_clipped_stats
import numpy as np
from PIL import Image as PILImage, ImageDraw, ImageFont
import dotenv

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
        "webcam_width": int(os.environ.get("WEBCAM_WIDTH", "0")) or None,  # 0 means use native
        "webcam_height": int(os.environ.get("WEBCAM_HEIGHT", "0")) or None,
        "webcam_warmup_frames": int(os.environ.get("WEBCAM_WARMUP_FRAMES", "5")),
    }


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
    
    Args:
        config: Configuration dictionary with webcam settings
        log: Logging function
    
    Returns:
        PIL.Image if capture successful, None otherwise
    """
    camera_index = config["webcam_index"]
    width = config["webcam_width"]
    height = config["webcam_height"]
    warmup_frames = config["webcam_warmup_frames"]
        
    # Open the camera
    cap = cv2.VideoCapture(camera_index)
    
    if not cap.isOpened():
        log(f"Error: Could not open camera at index {camera_index}")
        return None
    
    try:
        # Set resolution if specified
        if width is not None:
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        if height is not None:
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        
        # Get actual camera properties
        actual_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        actual_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # Warmup: skip initial frames to allow camera to adjust
        if warmup_frames > 0:
            log(f"Camera warmup: skipping {warmup_frames} frames...")
            for _ in range(warmup_frames):
                cap.read()
        
        # Capture the actual frame
        log("Capturing frame...")
        ret, frame = cap.read()
        
        if not ret or frame is None:
            log("Error: Failed to capture frame from camera")
            return None
        
        # Convert from BGR (OpenCV) to RGB (PIL)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Convert to PIL Image
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
    # Save image to temp file for Astrometry.net
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
        image.save(tmp, format='PNG')
        tmp_path = tmp.name
    
    try:
        # Perform plate solving
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
        # Clean up temp file
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
        
        # Calculate pixel scale from CD matrix
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


# =============================================================================
# Catalog queries
# =============================================================================

# Object type descriptions for LLM context
_OTYPE_DESCRIPTIONS = {
    'G': 'Galaxy', 'GiG': 'Galaxy in Group of Galaxies', 'GiC': 'Galaxy in Cluster of Galaxies',
    'GiP': 'Galaxy in Pair of Galaxies', 'AGN': 'Active Galactic Nucleus', 'QSO': 'Quasar',
    'Sy1': 'Seyfert 1 Galaxy', 'Sy2': 'Seyfert 2 Galaxy', 'SBG': 'Starburst Galaxy',
    'EmG': 'Emission-line Galaxy', 'LSB': 'Low Surface Brightness Galaxy', 'IG': 'Interacting Galaxies',
    '*': 'Star', '**': 'Double or Multiple Star', '*iC': 'Star in Cluster', '*iN': 'Star in Nebula',
    '*iA': 'Star in Association', 'V*': 'Variable Star', 'Ir*': 'Irregular Variable Star',
    'Or*': 'Orion Variable Star', 'Er*': 'Eruptive Variable Star', 'Ro*': 'Rotating Variable Star',
    'Pu*': 'Pulsating Variable Star', 'Ce*': 'Cepheid Variable', 'RR*': 'RR Lyrae Variable',
    'Mi*': 'Mira Variable', 'SN*': 'SuperNova', 'Cl*': 'Star Cluster', 'GlC': 'Globular Cluster',
    'OpC': 'Open Cluster', 'As*': 'Stellar Association', 'St*': 'Stellar Stream', 'MGr': 'Moving Group',
    'PN': 'Planetary Nebula', 'HII': 'HII Region', 'RNe': 'Reflection Nebula', 'SNR': 'SuperNova Remnant',
    'SR?': 'SuperNova Remnant Candidate', 'ISM': 'Interstellar Medium', 'Cld': 'Cloud',
    'DNe': 'Dark Nebula', 'EmO': 'Emission Object', 'Neb': 'Nebula', 'HH': 'Herbig-Haro Object',
    'WR*': 'Wolf-Rayet Star', 'Be*': 'Be Star', 'BS*': 'Blue Straggler Star', 'RG*': 'Red Giant Star',
    'WD*': 'White Dwarf', 'NS': 'Neutron Star', 'Psr': 'Pulsar', 'BH': 'Black Hole',
    'XB*': 'X-ray Binary', 'LXB': 'Low Mass X-ray Binary', 'HXB': 'High Mass X-ray Binary',
    'Pl': 'Planet', 'Pl?': 'Planet Candidate', 'Com': 'Comet', 'As': 'Asteroid',
}


def _query_objects(ra: float, dec: float, radius: float, mag_limit: float, log) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Query SIMBAD and Vizier for objects near the given coordinates.
    
    Returns:
         Tuple(objects, discarded_objects)
    """
    coord = SkyCoord(ra=ra * u.deg, dec=dec * u.deg, frame='icrs')
    
    objects = []
    discarded_objects = []
    seen_names = set()
    seen_hip_ids = set()
    seen_ngc_names = set()
    
    # Query SIMBAD
    log("Querying SIMBAD database...")
    try:
        custom_simbad = Simbad()
        # Add Gaia G magnitude (flux(G)) to fields
        custom_simbad.add_votable_fields('V', 'B', 'flux(G)', 'otype', 'otypes', 'sp', 'morphtype', 'dim', 'plx_value', 'ids')
        custom_simbad.ROW_LIMIT = 1000
        
        result = custom_simbad.query_region(coord, radius=radius * u.deg)
        
        if result is not None and len(result) > 0:
            log(f"  SIMBAD returned {len(result)} objects")
            for row in result:
                try:
                    name = str(row['main_id']).strip()
                    if not name:
                        continue
                    if name in seen_names:
                        discarded_objects.append({'name': name, 'reason': 'Duplicate name', 'source': 'SIMBAD'})
                        continue
                    
                    # Filter out IRAS and 2MASS objects (Infrared sources)
                    if name.startswith('IRAS') or name.startswith('2MASS'):
                        discarded_objects.append({'name': name, 'reason': 'Infrared source (IRAS/2MASS)', 'source': 'SIMBAD'})
                        continue
                    
                    # Get coordinates
                    obj_ra, obj_dec = None, None
                    if 'ra' in result.colnames and 'dec' in result.colnames:
                        ra_val, dec_val = row['ra'], row['dec']
                        if not np.ma.is_masked(ra_val) and not np.ma.is_masked(dec_val):
                            try:
                                obj_ra, obj_dec = float(ra_val), float(dec_val)
                            except (ValueError, TypeError):
                                try:
                                    c = SkyCoord(str(ra_val), str(dec_val), unit=(u.hourangle, u.deg))
                                    obj_ra, obj_dec = c.ra.deg, c.dec.deg
                                except:
                                    pass
                    
                    if obj_ra is None or obj_dec is None:
                        discarded_objects.append({'name': name, 'reason': 'Invalid coordinates', 'source': 'SIMBAD'})
                        continue
                    
                    # Get magnitudes
                    mag, mag_v, mag_b, mag_g = None, None, None, None
                    if 'V' in result.colnames and not np.ma.is_masked(row['V']):
                        mag_v = float(row['V'])
                        mag = mag_v
                    if 'B' in result.colnames and not np.ma.is_masked(row['B']):
                        mag_b = float(row['B'])
                        if mag is None:
                            mag = mag_b
                    # Check for Gaia G magnitude
                    if 'FLUX_G' in result.colnames and not np.ma.is_masked(row['FLUX_G']):
                        mag_g = float(row['FLUX_G'])
                        if mag is None:
                            mag = mag_g
                    
                    if mag is not None and mag > mag_limit:
                        discarded_objects.append({'name': name, 'reason': f'Fainter than mag limit ({mag:.2f} > {mag_limit})', 'mag': mag, 'source': 'SIMBAD'})
                        continue
                    
                    # If magnitude is unknown, skip unless it's a known Deep Sky catalog object
                    if mag is None and not (name.startswith('M ') or name.startswith('NGC') or name.startswith('IC')):
                        discarded_objects.append({'name': name, 'reason': 'No magnitude data and not a major DSO', 'source': 'SIMBAD'})
                        continue
                    
                    # Get object type
                    otype = str(row['otype']).strip() if 'otype' in result.colnames and not np.ma.is_masked(row['otype']) else ''
                    otype_description = _OTYPE_DESCRIPTIONS.get(otype, otype)
                    
                    # Get spectral type
                    spectral_type = None
                    if 'sp_type' in result.colnames and not np.ma.is_masked(row['sp_type']):
                        spectral_type = str(row['sp_type']).strip()
                    
                    # Get distance
                    distance_ly = None
                    if 'plx_value' in result.colnames and not np.ma.is_masked(row['plx_value']):
                        parallax = float(row['plx_value'])
                        if parallax > 0:
                            distance_ly = (1000 / parallax) * 3.26156
                    
                    # Get alternative names
                    alt_names = []
                    if 'ids' in result.colnames and not np.ma.is_masked(row['ids']):
                        alt_names = [n.strip() for n in str(row['ids']).split('|') if n.strip() and n.strip() != name][:10]
                    
                    # Determine catalog category
                    if name.startswith('M ') or name.startswith('M  '):
                        catalog = 'Messier'
                        name = name.replace('M  ', 'M').replace('M ', 'M')
                    elif name.startswith('NGC') or name.startswith('IC'):
                        catalog = 'NGC/IC'
                    elif '*' in otype or 'Star' in otype_description:
                        catalog = 'Star'
                    else:
                        catalog = 'Deep Sky'
                    
                    seen_names.add(name)
                    
                    obj_data = {
                        'name': name, 'ra': obj_ra, 'dec': obj_dec, 'mag': mag, 'catalog': catalog,
                        'object_type': otype, 'object_type_description': otype_description,
                        'spectral_type': spectral_type, 'distance_lightyears': distance_ly,
                        'magnitude_v': mag_v, 'magnitude_b': mag_b, 'magnitude_g': mag_g, 'alternative_names': alt_names
                    }
                    obj_data = {k: v for k, v in obj_data.items() if v is not None and v != '' and v != []}
                    objects.append(obj_data)
                    
                    # Track HIP/NGC IDs
                    for alt_name in alt_names:
                        alt_upper = alt_name.upper()
                        if alt_upper.startswith('HIP '):
                            try:
                                seen_hip_ids.add(int(alt_name.split()[1]))
                            except:
                                pass
                        elif alt_upper.startswith('NGC ') or alt_upper.startswith('IC '):
                            seen_ngc_names.add(alt_name.strip())
                    if name.upper().startswith('HIP '):
                        try:
                            seen_hip_ids.add(int(name.split()[1]))
                        except:
                            pass
                    elif name.upper().startswith('NGC ') or name.upper().startswith('IC '):
                        seen_ngc_names.add(name.strip())
                        
                except Exception:
                    continue
    except Exception as e:
        log(f"  Error querying SIMBAD: {e}")
    
    # Query Hipparcos catalog
    log("Querying Hipparcos catalog...")
    try:
        v = Vizier(columns=['HIP', 'Vmag', 'RAhms', 'DEdms', '_RAJ2000', '_DEJ2000'], row_limit=300)
        v.column_filters = {"Vmag": f"<{mag_limit}"}
        result = v.query_region(coord, radius=radius * u.deg, catalog="I/239/hip_main")
        
        if result and len(result) > 0:
            table = result[0]
            log(f"  Hipparcos returned {len(table)} stars")
            hip_added = 0
            for row in table:
                try:
                    hip = int(row['HIP'])
                    name = f"HIP {hip}"
                    
                    if name in seen_names or hip in seen_hip_ids:
                        discarded_objects.append({'name': name, 'reason': 'Duplicate (already in SIMBAD)', 'source': 'Hipparcos'})
                        continue
                    
                    obj_ra = float(row['_RAJ2000'])
                    obj_dec = float(row['_DEJ2000'])
                    mag = float(row['Vmag']) if not np.ma.is_masked(row['Vmag']) else None
                    
                    if mag is not None and mag > mag_limit:
                        discarded_objects.append({'name': name, 'reason': f'Fainter than mag limit ({mag:.2f} > {mag_limit})', 'mag': mag, 'source': 'Hipparcos'})
                        continue
                    
                    seen_names.add(name)
                    objects.append({'name': name, 'ra': obj_ra, 'dec': obj_dec, 'mag': mag, 'catalog': 'Star'})
                    hip_added += 1
                except Exception:
                    continue
            log(f"  Added {hip_added} from Hipparcos")
    except Exception as e:
        log(f"  Error querying Hipparcos: {e}")
    
    # Query OpenNGC
    log("Querying OpenNGC catalog...")
    try:
        v = Vizier(columns=['Name', 'RAJ2000', 'DEJ2000', 'V-Mag', 'B-Mag'], row_limit=300)
        result = v.query_region(coord, radius=radius * u.deg, catalog="VII/118/ngc2000")
        
        if result and len(result) > 0:
            table = result[0]
            log(f"  OpenNGC returned {len(table)} objects")
            ngc_added = 0
            for row in table:
                try:
                    name = str(row['Name']).strip()
                    if not name:
                        continue
                        
                    if name in seen_names or name in seen_ngc_names:
                        discarded_objects.append({'name': name, 'reason': 'Duplicate', 'source': 'OpenNGC'})
                        continue
                    
                    if '_RAJ2000' not in table.colnames:
                        continue
                    
                    obj_ra = float(row['_RAJ2000'])
                    obj_dec = float(row['_DEJ2000'])
                    
                    mag = None
                    for mag_col in ['V-Mag', 'B-Mag']:
                        if mag_col in table.colnames and not np.ma.is_masked(row[mag_col]):
                            mag = float(row[mag_col])
                            break
                    
                    if mag is not None and mag > mag_limit:
                        discarded_objects.append({'name': name, 'reason': f'Fainter than mag limit ({mag:.2f} > {mag_limit})', 'mag': mag, 'source': 'OpenNGC'})
                        continue
                    
                    catalog = 'Messier' if name.startswith('M') else 'NGC/IC'
                    seen_names.add(name)
                    objects.append({'name': name, 'ra': obj_ra, 'dec': obj_dec, 'mag': mag, 'catalog': catalog})
                    ngc_added += 1
                except Exception:
                    continue
            log(f"  Added {ngc_added} from OpenNGC")
    except Exception as e:
        log(f"  Error querying OpenNGC: {e}")
    
    log(f"Total unique objects found: {len(objects)}")
    return objects, discarded_objects


# =============================================================================
# Limiting Magnitude Calculation
# =============================================================================

def _estimate_limiting_magnitude(image: PILImage.Image, wcs_header, log) -> float:
    """
    Estimate the limiting magnitude of the image by checking for the presence
    of catalog stars from Tycho-2.
    
    Returns:
        float: Estimated limiting magnitude (default 8.0 if estimation fails)
    """
    try:
        # Convert to grayscale numpy array
        img_array = np.array(image.convert('L'))
        height, width = img_array.shape
        
        # Calculate background statistics (mean and std dev)
        # using sigma clipping to ignore bright stars
        try:
            mean, median, std = sigma_clipped_stats(img_array, sigma=3.0)
        except Exception:
            # Fallback if sigma_clipped_stats fails
            mean = np.mean(img_array)
            median = np.median(img_array)
            std = np.std(img_array)
            
        threshold = median + 3 * std
        log(f"Background estimation: median={median:.1f}, std={std:.1f}, threshold={threshold:.1f}")
        
        # Get center coordinates
        if 'CRVAL1' in wcs_header and 'CRVAL2' in wcs_header:
            ra = float(wcs_header['CRVAL1'])
            dec = float(wcs_header['CRVAL2'])
        else:
            return 8.0
            
        # Calculate approximate radius
        pixel_scale_deg = 0
        if 'CD1_1' in wcs_header:
             pixel_scale_deg = abs(wcs_header['CD1_1'])
        elif 'CDELT1' in wcs_header:
             pixel_scale_deg = abs(wcs_header['CDELT1'])
             
        if pixel_scale_deg == 0:
            return 8.0
            
        diag_pixels = np.sqrt(width**2 + height**2)
        radius_deg = (diag_pixels * pixel_scale_deg) / 2
        
        # Query Tycho-2 (I/259/tyc2) for reference stars
        # We query deeper than we expect (up to mag 12) to find the drop-off
        v = Vizier(columns=['VTmag', '_RAJ2000', '_DEJ2000'], row_limit=2000)
        v.column_filters = {"VTmag": "<12"} 
        coord = SkyCoord(ra=ra*u.deg, dec=dec*u.deg, frame='icrs')
        result = v.query_region(coord, radius=radius_deg*u.deg, catalog="I/259/tyc2")
        
        if not result or len(result) == 0:
            log("No reference stars found for calibration. Defaulting to 8.0")
            return 8.0
            
        table = result[0]
        wcs = WCS(wcs_header)
        
        detected_mags = []
        
        for row in table:
            try:
                # Check if VTmag exists
                if np.ma.is_masked(row['VTmag']):
                    continue
                    
                mag = float(row['VTmag'])
                sky_coord = SkyCoord(ra=row['_RAJ2000']*u.deg, dec=row['_DEJ2000']*u.deg, frame='icrs')
                px, py = wcs.world_to_pixel(sky_coord)
                
                # Check bounds (ignore edge stars)
                margin = 5
                if margin <= px < width - margin and margin <= py < height - margin:
                    # Look for max pixel value in a small window (5x5) around predicted pos
                    x_int, y_int = int(px), int(py)
                    window = img_array[y_int-2:y_int+3, x_int-2:x_int+3]
                    peak_val = np.max(window)
                    
                    if peak_val > threshold:
                        detected_mags.append(mag)
            except Exception:
                continue
                
        if not detected_mags:
            log("No stars detected from reference catalog. Image might be too dark or cloudy.")
            return 6.0 
            
        # Sort detected magnitudes and take the 95th percentile as the limit
        # This assumes we detect most stars up to the limit and then it drops off
        limit = np.percentile(detected_mags, 95)
        
        # Apply a sanity cap (e.g. if we detected a mag 11 star, maybe limit is 11.5)
        log(f"Detected {len(detected_mags)} stars. 95th percentile magnitude: {limit:.2f}")
        return float(limit)

    except Exception as e:
        log(f"Error estimating magnitude limit: {e}")
        return 8.0


# =============================================================================
# Image annotation
# =============================================================================

def _annotate_image(image: PILImage.Image, wcs_header, objects: List[Dict], log) -> Tuple[PILImage.Image, List[Dict]]:
    """
    Annotate the image with found objects.
    
    Returns:
        Tuple of (annotated PIL.Image, list of objects that were drawn)
    """
    img = image.convert('RGB').copy()
    draw = ImageDraw.Draw(img)
    wcs = WCS(wcs_header)
    
    # Try to load a font, fallback to default
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
    
    colors = {
        'Messier': (255, 100, 100),
        'NGC/IC': (100, 255, 100),
        'Star': (100, 200, 255),
        'Deep Sky': (255, 200, 100),
        'default': (255, 255, 100)
    }
    
    annotated_objects = []
    
    for obj in objects:
        try:
            sky_coord = SkyCoord(ra=obj['ra'] * u.deg, dec=obj['dec'] * u.deg, frame='icrs')
            pixel_coords = wcs.world_to_pixel(sky_coord)
            x, y = float(pixel_coords[0]), float(pixel_coords[1])
            
            if 0 <= x < img_width and 0 <= y < img_height:
                color = colors.get(obj.get('catalog', 'default'), colors['default'])
                
                radius = 15
                draw.ellipse([(x - radius, y - radius), (x + radius, y + radius)], outline=color, width=2)
                
                label = obj['name']
                if obj.get('mag') is not None:
                    label += f" ({obj['mag']:.1f})"
                
                label_x, label_y = x + radius + 5, y - 7
                bbox = draw.textbbox((label_x, label_y), label, font=font_small)
                draw.rectangle([bbox[0] - 2, bbox[1] - 1, bbox[2] + 2, bbox[3] + 1], fill=(0, 0, 0, 180))
                draw.text((label_x, label_y), label, fill=color, font=font_small)
                
                annotated_objects.append(obj)
        except Exception:
            continue
    
    # Add legend
    legend_y = 10
    draw.rectangle([5, 5, 180, 95], fill=(0, 0, 0, 200), outline=(255, 255, 255))
    draw.text((10, legend_y), "Legend:", fill=(255, 255, 255), font=font)
    legend_y += 18
    for catalog, color in colors.items():
        if catalog != 'default':
            draw.text((10, legend_y), f"● {catalog}", fill=color, font=font_small)
            legend_y += 15
    
    log(f"Annotated {len(annotated_objects)} objects on image ({img.size[0]}x{img.size[1]} px)")
    return img, annotated_objects


# =============================================================================
# Main API function
# =============================================================================

def analyze_image(
    radius: Optional[float] = None,
    mag_limit: Optional[float] = None,
    verbose: bool = False
) -> Dict[str, Any]:
    """
    Capture an image from webcam and analyze it using plate solving and catalog queries.
    
    This is the main API function for use as a tool in Google ADK agents.
    It captures an image from a webcam (physical or virtual like OBS), performs 
    plate solving to determine sky coordinates, queries astronomical catalogs 
    for celestial objects, and returns the annotated image along with metadata.
    
    The webcam can be:
    - A physical camera connected to a telescope
    - A virtual camera (e.g., OBS Virtual Camera streaming from Stellarium)
    
    Args:
        radius: Search radius in degrees for catalog queries. 
                If None, auto-calculated from the image's field of view.
                Default: None (auto-calculate)
        mag_limit: Limiting magnitude for object search. Objects fainter than
                this magnitude are excluded. 
                If None, auto-calculated from image statistics.
                Default: None (auto-calculate)
        verbose: Whether to print progress messages. Default: False
    
    Returns:
        A dictionary containing:
        - success: bool - Whether the analysis succeeded
        - error: str - Error message if success is False
        - captured_image: PIL.Image - The raw captured image from webcam
        - annotated_image: PIL.Image - The image with objects marked and labeled
        - plate_solving: dict - Center coordinates, FOV, and pixel scale
        - objects: dict - Count and list of identified celestial objects
    
    Configuration (via environment variables):
        ASTROMETRY_API_KEY: API key for Astrometry.net (required)
        ASTROMETRY_TIMEOUT: Timeout in seconds for plate solving (default: 120)
        
        WEBCAM_INDEX: Camera device index (default: 0)
        WEBCAM_WIDTH: Capture width in pixels (default: camera native)
        WEBCAM_HEIGHT: Capture height in pixels (default: camera native)
        WEBCAM_WARMUP_FRAMES: Frames to skip for warmup (default: 5)
    
    Example:
        >>> from analyze_image_tool import analyze_image
        >>> 
        >>> # Capture from webcam (configured via WEBCAM_INDEX env var) and analyze
        >>> result = analyze_image(mag_limit=10.0)
        >>> 
        >>> if result["success"]:
        ...     annotated = result["annotated_image"]
        ...     print(f"Found {result['objects']['count']} objects")
        ...     print(f"Center: {result['plate_solving']['center']['ra_hms']}")
        ... else:
        ...     print(f"Error: {result['error']}")
    """
    # Create logger function
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
    
    # Step 1: Capture from webcam
    log("> Step 1: Capturing image from webcam...")
    image = _capture_from_webcam(config, log)
    
    if image is None:
        return {
            "success": False,
            "error": f"Failed to capture image from webcam at index {config['webcam_index']}. "
                     f"Use _list_available_cameras() to see available devices."
        }
    
    # Keep a copy of the original captured image
    captured_image = image.copy()
    
    # Step 2: Plate solve
    log("\n > Step 2: Plate solving...")
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
        log(f"Field of view: {fov_width*60:.1f}' x {fov_height*60:.1f}' (diagonal: {fov_diagonal*60:.1f}')")
        if radius is None:
            radius = fov_diagonal / 2
            log(f"Auto-calculated search radius: {radius:.3f}°")
    else:
        if radius is None:
            radius = 1.0
            log(f"Could not calculate FOV, using default radius: {radius}°")
    
    # Calculate pixel scale
    pixel_scale_arcsec = None
    if 'CD1_1' in wcs_header:
        pixel_scale_arcsec = abs(wcs_header['CD1_1']) * 3600
    elif 'CDELT1' in wcs_header:
        pixel_scale_arcsec = abs(wcs_header['CDELT1']) * 3600

    # Auto-calculate mag_limit if needed
    log("Step 3: Estimating limiting magnitude from image statistics...")
    if mag_limit is None:
        mag_limit = _estimate_limiting_magnitude(image, wcs_header, log)
    else:
        log(f"Using user-specified limiting magnitude: {mag_limit}")
    
    # Step 3: Query catalogs
    log("\n> Step 4: Querying astronomical catalogs...")
    objects, discarded_objects = _query_objects(ra, dec, radius, mag_limit, log)
    
    # Step 4: Annotate image
    log("\n> Step 5: Annotating image...")
    annotated_image, annotated_objects = _annotate_image(image, wcs_header, objects, log)

    # Build simplified objects list for output
    objects_for_output = []
    for obj in annotated_objects:
        obj_data = {
            "name": obj['name'],
            "type": obj.get('catalog', 'Unknown'),
        }
        
        if obj.get('mag') is not None:
            obj_data["magnitude_visual"] = round(obj['mag'], 2)
        if obj.get('spectral_type'):
            obj_data["spectral_type"] = obj['spectral_type']
        if obj.get('distance_lightyears'):
            obj_data["distance_lightyears"] = round(obj['distance_lightyears'], 1)
        
        obj_type_desc = obj.get('object_type_description', '')
        if obj_type_desc and obj_type_desc != 'Star':
            obj_data["subtype"] = obj_type_desc
        
        objects_for_output.append(obj_data)
    
    # Build FOV data
    fov_data = None
    if fov_width is not None:
        fov_data = {
            "width_deg": round(fov_width, 6),
            "height_deg": round(fov_height, 6),
            "diagonal_deg": round(fov_diagonal, 6),
            "width_arcmin": round(fov_width * 60, 2),
            "height_arcmin": round(fov_height * 60, 2),
            "diagonal_arcmin": round(fov_diagonal * 60, 2)
        }
    
    # Save results to a timestamped folder
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        captures_dir = os.path.join(os.path.dirname(__file__), "..", "..", "tmp", "captures", timestamp)
        os.makedirs(captures_dir, exist_ok=True)
        
        # Save captured image
        captured_path = os.path.join(captures_dir, "captured.png")
        captured_image.save(captured_path)
        
        # Save annotated image
        annotated_path = os.path.join(captures_dir, "annotated.png")
        annotated_image.save(annotated_path)
        
        # Save JSON output (only plate_solving and objects)
        output_json = {
            "plate_solving": {
                "center": {
                    "ra_deg": round(ra, 6),
                    "dec_deg": round(dec, 6),
                    "ra_hms": _ra_to_hms(ra),
                    "dec_dms": _dec_to_dms(dec)
                },
                "pixel_scale_arcsec": round(pixel_scale_arcsec, 4) if pixel_scale_arcsec else None,
                "field_of_view": fov_data
            },
            "objects": {
                "count": len(objects_for_output),
                "items": objects_for_output,
                "discarded": discarded_objects
            }
        }
        
        json_path = os.path.join(captures_dir, "analysis.json")
        with open(json_path, "w") as f:
            json.dump(output_json, f, indent=2)
            
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
        },
        "objects": {
            "count": len(objects_for_output),
            "items": objects_for_output,
            "discarded": discarded_objects
        }
    }
