"""
Astronomical image annotator using Astrometry.net plate solving and Vizier catalogs.

This module provides the analyze_image function for use as a tool in Google ADK agents.
It receives a PIL Image, performs plate solving and catalog queries, and returns
the annotated image along with metadata about the celestial objects found.

Configuration via environment variables:
    ASTROMETRY_API_KEY: API key for Astrometry.net (required)
    ASTROMETRY_TIMEOUT: Timeout in seconds for plate solving (default: 120)
    ASTROMETRY_USE_CACHE: Whether to cache plate solving results (default: true)

Usage:
    from annotator import analyze_image
    from PIL import Image
    
    img = Image.open("telescope_image.png")
    result = analyze_image(img, radius=1.5, mag_limit=8.0)
    
    if result["success"]:
        annotated_img = result["annotated_image"]  # PIL.Image
        objects = result["objects"]  # List of celestial objects
"""

import os
import io
import hashlib
import pickle
import tempfile
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple

from astroquery.astrometry_net import AstrometryNet
from astroquery.vizier import Vizier
from astroquery.simbad import Simbad
from astropy.coordinates import SkyCoord
from astropy.wcs import WCS
import astropy.units as u
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
        "api_key": os.environ.get("ASTROMETRY_API_KEY"),
        "timeout": int(os.environ.get("ASTROMETRY_TIMEOUT", "120")),
        "use_cache": os.environ.get("ASTROMETRY_USE_CACHE", "true").lower() in ("true", "1", "yes"),
        "cache_dir": os.environ.get("ASTROMETRY_CACHE_DIR", tempfile.gettempdir()),
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


def _get_image_hash(image: PILImage.Image) -> str:
    """Generate a hash of the image for caching purposes."""
    img_bytes = io.BytesIO()
    image.save(img_bytes, format='PNG')
    return hashlib.md5(img_bytes.getvalue()).hexdigest()[:12]


def _get_cache_path(image: PILImage.Image, cache_dir: str) -> str:
    """Get the cache file path for a given image."""
    image_hash = _get_image_hash(image)
    return os.path.join(cache_dir, f".platesolve_cache_{image_hash}.pkl")


# =============================================================================
# Plate solving
# =============================================================================

def _plate_solve(image: PILImage.Image, api_key: str, timeout: int, use_cache: bool, cache_dir: str, log):
    """
    Perform plate solving on an image using Astrometry.net.
    Results are cached to avoid re-solving the same image.
    
    Returns:
        WCS header if successful, None otherwise
    """
    cache_path = _get_cache_path(image, cache_dir)
    
    # Try to load from cache
    if use_cache and os.path.exists(cache_path):
        try:
            with open(cache_path, 'rb') as f:
                cached_data = pickle.load(f)
            log(f"Loaded plate solving results from cache: {cache_path}")
            return cached_data['wcs_header']
        except Exception as e:
            log(f"Failed to load cache, re-solving: {e}")
    
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
            log("Plate solving successful!")
            # Save to cache
            if use_cache:
                try:
                    cache_data = {
                        'wcs_header': wcs_header,
                        'timestamp': datetime.now().isoformat()
                    }
                    with open(cache_path, 'wb') as f:
                        pickle.dump(cache_data, f)
                    log(f"Cached plate solving results to: {cache_path}")
                except Exception as e:
                    log(f"Warning: Failed to cache results: {e}")
            
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


def _query_objects(ra: float, dec: float, radius: float, mag_limit: float, log) -> List[Dict[str, Any]]:
    """
    Query SIMBAD and Vizier for objects near the given coordinates.
    
    Returns:
        List of objects with name, ra, dec, magnitude, and other metadata
    """
    coord = SkyCoord(ra=ra * u.deg, dec=dec * u.deg, frame='icrs')
    
    objects = []
    seen_names = set()
    seen_hip_ids = set()
    seen_ngc_names = set()
    
    # Query SIMBAD
    log("Querying SIMBAD database...")
    try:
        custom_simbad = Simbad()
        custom_simbad.add_votable_fields('V', 'B', 'otype', 'otypes', 'sp', 'morphtype', 'dim', 'plx_value', 'ids')
        custom_simbad.ROW_LIMIT = 500
        
        result = custom_simbad.query_region(coord, radius=radius * u.deg)
        
        if result is not None and len(result) > 0:
            log(f"  SIMBAD returned {len(result)} objects")
            for row in result:
                try:
                    name = str(row['main_id']).strip()
                    if not name or name in seen_names:
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
                                    continue
                    
                    if obj_ra is None or obj_dec is None:
                        continue
                    
                    # Get magnitudes
                    mag, mag_v, mag_b = None, None, None
                    if 'V' in result.colnames and not np.ma.is_masked(row['V']):
                        mag_v = float(row['V'])
                        mag = mag_v
                    if 'B' in result.colnames and not np.ma.is_masked(row['B']):
                        mag_b = float(row['B'])
                        if mag is None:
                            mag = mag_b
                    
                    if mag is not None and mag > mag_limit:
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
                        'magnitude_v': mag_v, 'magnitude_b': mag_b, 'alternative_names': alt_names
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
                        continue
                    
                    obj_ra = float(row['_RAJ2000'])
                    obj_dec = float(row['_DEJ2000'])
                    mag = float(row['Vmag']) if not np.ma.is_masked(row['Vmag']) else None
                    
                    if mag is not None and mag > mag_limit:
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
                    if not name or name in seen_names or name in seen_ngc_names:
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
    return objects


# =============================================================================
# Image annotation
# =============================================================================

def _annotate_image(image: PILImage.Image, wcs_header, objects: List[Dict], log) -> Tuple[PILImage.Image, List[Dict]]:
    """
    Annotate the image with found objects.
    
    Returns:
        Tuple of (annotated PIL.Image, list of objects that were drawn)
    """
    log("Annotating image...")
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
    image: PILImage.Image,
    radius: Optional[float] = None,
    mag_limit: float = 8.0,
    verbose: bool = False
) -> Dict[str, Any]:
    """
    Analyze an astronomical image using plate solving and catalog queries.
    
    This is the main API function for use as a tool in Google ADK agents.
    It receives a PIL Image, performs plate solving to determine sky coordinates,
    queries astronomical catalogs for celestial objects, and returns the
    annotated image along with metadata.
    
    Args:
        image: PIL.Image object containing the telescope image to analyze.
        radius: Search radius in degrees for catalog queries. 
                If None, auto-calculated from the image's field of view.
                Default: None (auto-calculate)
        mag_limit: Limiting magnitude for object search. Objects fainter than
                   this magnitude are excluded. Lower values = fewer but brighter
                   objects. Default: 8.0
        verbose: Whether to print progress messages. Default: False
    
    Returns:
        A dictionary containing:
        - success: bool - Whether the analysis succeeded
        - error: str - Error message if success is False
        - annotated_image: PIL.Image - The image with objects marked and labeled
        - plate_solving: dict - Center coordinates, FOV, and pixel scale
        - objects: dict - Count and list of identified celestial objects
    
    Configuration (via environment variables):
        ASTROMETRY_API_KEY: API key for Astrometry.net (required)
        ASTROMETRY_TIMEOUT: Timeout in seconds for plate solving (default: 120)
        ASTROMETRY_USE_CACHE: Cache plate solving results (default: true)
        ASTROMETRY_CACHE_DIR: Directory for cache files (default: system temp)
    
    Example:
        >>> from annotator import analyze_image
        >>> from PIL import Image
        >>> 
        >>> img = Image.open("telescope_capture.png")
        >>> result = analyze_image(img, mag_limit=10.0)
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
    
    # Step 1: Plate solve
    wcs_header = _plate_solve(
        image, 
        config["api_key"], 
        config["timeout"], 
        config["use_cache"],
        config["cache_dir"],
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
    
    log(f"Searching for objects (radius={radius:.3f}°, mag_limit={mag_limit})")
    
    # Step 2: Query catalogs
    objects = _query_objects(ra, dec, radius, mag_limit, log)
    
    # Step 3: Annotate image
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
    
    log(f"Analysis complete! Found {len(objects_for_output)} objects in the field of view.")
    
    return {
        "success": True,
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
            "items": objects_for_output
        }
    }
