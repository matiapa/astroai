"""
SIMBAD position-specific query module.

Provides functions to query SIMBAD for objects at specific celestial coordinates,
used to identify detected objects after plate-solving.
"""

from typing import Optional, Dict, Any, List
from astroquery.simbad import Simbad
from astropy.coordinates import SkyCoord
import astropy.units as u
import numpy as np


# Object type descriptions for human-readable output
OTYPE_DESCRIPTIONS = {
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


def query_simbad_at_position(
    ra: float,
    dec: float,
    radius_arcsec: float = 10.0
) -> Optional[Dict[str, Any]]:
    """
    Query SIMBAD for the closest object at a specific position.
    
    Args:
        ra: Right Ascension in degrees
        dec: Declination in degrees
        radius_arcsec: Search radius in arcseconds (default 10")
    
    Returns:
        Dictionary with object information if found, None otherwise.
        Contains: name, ra, dec, object_type, magnitude, distance info, etc.
    """
    try:
        coord = SkyCoord(ra=ra * u.deg, dec=dec * u.deg, frame='icrs')
        
        # Configure SIMBAD query with selected fields
        # Balance between data richness and query speed
        custom_simbad = Simbad()
        custom_simbad.add_votable_fields(
            'otype',       # Object type code (e.g., '*', 'G')
            'V',           # Visual magnitude
            'B',           # Blue magnitude (for B-V color index)
            'sp_type',     # Spectral type (e.g., 'G2V')
            'morph_type',  # Morphological type (for galaxies)
            'plx_value'    # Parallax (for distance calculation)
        )
        custom_simbad.ROW_LIMIT = 5  # We only need the closest matches
        
        # Query with specified radius
        result = custom_simbad.query_region(
            coord, 
            radius=radius_arcsec * u.arcsec
        )
        
        if result is None or len(result) == 0:
            return None
        
        # Find the closest object
        closest_row = None
        min_distance = float('inf')
        
        for row in result:
            try:
                # Get object coordinates
                if 'ra' in result.colnames and 'dec' in result.colnames:
                    ra_val, dec_val = row['ra'], row['dec']
                    if not np.ma.is_masked(ra_val) and not np.ma.is_masked(dec_val):
                        try:
                            obj_ra, obj_dec = float(ra_val), float(dec_val)
                        except (ValueError, TypeError):
                            # Try parsing as sexagesimal
                            try:
                                c = SkyCoord(str(ra_val), str(dec_val), unit=(u.hourangle, u.deg))
                                obj_ra, obj_dec = c.ra.deg, c.dec.deg
                            except:
                                continue
                        
                        # Calculate angular distance
                        obj_coord = SkyCoord(ra=obj_ra * u.deg, dec=obj_dec * u.deg, frame='icrs')
                        sep = coord.separation(obj_coord).arcsec
                        
                        if sep < min_distance:
                            min_distance = sep
                            closest_row = row
            except Exception:
                continue
        
        if closest_row is None:
            return None
        
        # Parse the closest object
        return _parse_simbad_row(closest_row, result.colnames, min_distance)
        
    except Exception as e:
        # Query failed - return None silently
        return None


def _parse_simbad_row(row, colnames: List[str], separation_arcsec: float) -> Dict[str, Any]:
    """
    Parse a SIMBAD result row into a structured dictionary.
    """
    # Get main identifier
    name = str(row['main_id']).strip()
    
    # Clean up name formatting
    if name.startswith('M  '):
        name = 'M' + name[3:].strip()
    elif name.startswith('M '):
        name = 'M' + name[2:].strip()
    
    # Get coordinates
    obj_ra, obj_dec = None, None
    if 'ra' in colnames and 'dec' in colnames:
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
    
    # Get magnitudes
    mag = None
    mag_v = None
    mag_b = None
    mag_g = None
    
    if 'V' in colnames and not np.ma.is_masked(row['V']):
        mag_v = float(row['V'])
        mag = mag_v
    if 'B' in colnames and not np.ma.is_masked(row['B']):
        mag_b = float(row['B'])
        if mag is None:
            mag = mag_b
    if 'FLUX_G' in colnames and not np.ma.is_masked(row['FLUX_G']):
        mag_g = float(row['FLUX_G'])
        if mag is None:
            mag = mag_g
    
    # Get object type
    otype = ''
    otype_description = ''
    if 'otype' in colnames and not np.ma.is_masked(row['otype']):
        otype = str(row['otype']).strip()
        otype_description = OTYPE_DESCRIPTIONS.get(otype, otype)
    
    # Get spectral type
    spectral_type = None
    if 'sp_type' in colnames and not np.ma.is_masked(row['sp_type']):
        spectral_type = str(row['sp_type']).strip()
    
    # Get distance from parallax
    distance_ly = None
    if 'plx_value' in colnames and not np.ma.is_masked(row['plx_value']):
        parallax = float(row['plx_value'])
        if parallax > 0:
            distance_ly = round((1000 / parallax) * 3.26156, 1)
    
    # Calculate B-V color index (indicates stellar temperature/color)
    # B-V < 0: Blue/hot, ~0.65: Yellow like Sun, > 1.0: Red/cool
    bv_index = None
    if mag_b is not None and mag_v is not None:
        bv_index = round(mag_b - mag_v, 2)
    
    # Get morphological type (for galaxies)
    morph_type = None
    if 'morph_type' in colnames and not np.ma.is_masked(row['morph_type']):
        morph_type = str(row['morph_type']).strip()
    
    # Get alternative names
    alt_names = []
    if 'ids' in colnames and not np.ma.is_masked(row['ids']):
        alt_names = [n.strip() for n in str(row['ids']).split('|') 
                     if n.strip() and n.strip() != name][:10]
    
    # Determine catalog category
    if name.startswith('M') and name[1:].strip().isdigit():
        catalog = 'Messier'
    elif name.startswith('NGC') or name.startswith('IC'):
        catalog = 'NGC/IC'
    elif '*' in otype or 'Star' in otype_description:
        catalog = 'Star'
    else:
        catalog = 'Deep Sky'
    
    # Build result dictionary
    obj_data = {
        'name': name,
        'ra': obj_ra,
        'dec': obj_dec,
        'mag': mag,
        'catalog': catalog,
        'object_type': otype,
        'object_type_description': otype_description,
        'spectral_type': spectral_type,
        'morphological_type': morph_type,
        'distance_lightyears': distance_ly,
        'magnitude_v': mag_v,
        'magnitude_b': mag_b,
        'bv_color_index': bv_index,
        'alternative_names': alt_names,
        'match_separation_arcsec': round(separation_arcsec, 2)
    }
    
    # Remove None/empty values (handle numpy arrays specially)
    def is_empty(v):
        if v is None:
            return True
        if isinstance(v, str) and v == '':
            return True
        if isinstance(v, list) and len(v) == 0:
            return True
        return False
    
    obj_data = {k: v for k, v in obj_data.items() if not is_empty(v)}
    
    return obj_data


def query_simbad_batch(
    positions: List[tuple],
    radius_arcsec: float = 10.0,
    max_workers: int = 10,
    show_progress: bool = True
) -> List[Optional[Dict[str, Any]]]:
    """
    Query SIMBAD for multiple positions in parallel.
    
    Args:
        positions: List of (ra, dec) tuples in degrees
        radius_arcsec: Search radius for each position
        max_workers: Maximum number of parallel queries
        show_progress: Whether to show tqdm progress bar
    
    Returns:
        List of results, one per position (None if no match)
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed
    from tqdm import tqdm
    
    if not positions:
        return []
    
    # Create a mapping from index to position for ordered results
    results = [None] * len(positions)
    
    def query_position(args):
        idx, (ra, dec) = args
        result = query_simbad_at_position(ra, dec, radius_arcsec)
        return idx, result
    
    # Run queries in parallel
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(query_position, (i, pos)): i 
            for i, pos in enumerate(positions)
        }
        
        # Use tqdm for progress tracking
        iterator = as_completed(futures)
        if show_progress:
            iterator = tqdm(
                iterator, 
                total=len(positions), 
                desc="Querying SIMBAD",
                unit="pos"
            )
        
        for future in iterator:
            try:
                idx, result = future.result()
                results[idx] = result
            except Exception:
                pass  # Keep None for failed queries
    
    return results

