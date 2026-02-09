import os
import sys
import json
import logging

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.config import get_config_from_env
from src.tools.capture_sky.simbad_query import query_simbad_by_id

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def complete_cache():
    config = get_config_from_env()
    cache_path = os.path.join('src', 'tools', 'capture_sky', 'analysis_cache.json')
    
    if not os.path.exists(cache_path):
        logger.error(f"Cache file not found at {cache_path}")
        return

    with open(cache_path, 'r') as f:
        cache = json.load(f)

    updated_any = False

    for image_hash, result in cache.items():
        logger.info(f"Processing image hash: {image_hash}")
        identified_objects = result.get('identified_objects', [])
        
        for obj in identified_objects:
            name = obj.get('name')
            # Check if it needs completion (e.g., missing celestial_coords or type)
            if name and ('celestial_coords' not in obj or 'type' not in obj):
                logger.info(f"  Querying SIMBAD for: {name}")
                simbad_obj = query_simbad_by_id(name, config)
                
                # If it fails, try adding a space for common catalogs (M, NGC, IC)
                if not simbad_obj:
                    import re
                    match = re.match(r'^([A-Z]+)(\d+)$', name)
                    if match:
                        alt_name = f"{match.group(1)} {match.group(2)}"
                        logger.info(f"    Failed. Trying alternative format: {alt_name}")
                        simbad_obj = query_simbad_by_id(alt_name, config)
                
                if simbad_obj:
                    # Map CelestialObject fields to the JSON structure
                    obj['type'] = simbad_obj.catalog
                    obj['subtype'] = simbad_obj.object_type_description
                    obj['celestial_coords'] = {
                        'ra_deg': round(simbad_obj.position.ra, 6),
                        'dec_deg': round(simbad_obj.position.dec, 6),
                        'radius_arcsec': round(simbad_obj.position.radius_arcsec, 2)
                    }
                    
                    # Add optional fields
                    if simbad_obj.alternative_names:
                        obj['alternative_names'] = simbad_obj.alternative_names
                    if simbad_obj.magnitude_visual:
                        obj['magnitude_visual'] = round(simbad_obj.magnitude_visual, 2)
                    if simbad_obj.bv_color_index:
                        obj['bv_color_index'] = round(simbad_obj.bv_color_index, 2)
                    if simbad_obj.spectral_type:
                        obj['spectral_type'] = simbad_obj.spectral_type
                    if simbad_obj.morphological_type:
                        obj['morphological_type'] = simbad_obj.morphological_type
                    if simbad_obj.distance_lightyears:
                        obj['distance_lightyears'] = simbad_obj.distance_lightyears
                        
                    logger.info(f"    Completed data for {name}")
                    updated_any = True
                else:
                    logger.warning(f"    Could not find '{name}' in SIMBAD")

        # After completing objects, check if plate_solving needs to be generated
        if 'plate_solving' not in result or not result['plate_solving']:
            # Find the first object that has celestial coordinates
            first_obj_with_coords = next((obj for obj in identified_objects if 'celestial_coords' in obj), None)
            
            if first_obj_with_coords:
                coords = first_obj_with_coords['celestial_coords']
                result['plate_solving'] = {
                    'center_ra_deg': coords['ra_deg'],
                    'center_dec_deg': coords['dec_deg'],
                    'pixel_scale_arcsec': 5.0
                }
                logger.info(f"  Generated plate solving info using '{first_obj_with_coords['name']}' coordinates")
                updated_any = True
            else:
                logger.warning("  Could not generate plate solving info: No objects with celestial coordinates found")
        else:
            # Ensure pixel_scale_arcsec is set to 5.0 if requested (or just ensure it's present)
            if 'pixel_scale_arcsec' not in result['plate_solving']:
                result['plate_solving']['pixel_scale_arcsec'] = 5.0
                updated_any = True

    if updated_any:
        with open(cache_path, 'w') as f:
            json.dump(cache, f, indent=4)
        logger.info(f"Successfully updated {cache_path}")
    else:
        logger.info("No updates needed.")

if __name__ == "__main__":
    complete_cache()
