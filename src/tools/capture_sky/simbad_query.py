"""
SIMBAD position-specific query module.

Provides functions to query SIMBAD for objects at specific celestial coordinates,
used to identify detected objects after plate-solving.
"""

from typing import Optional, List, cast
from astroquery.simbad import Simbad
from astropy.coordinates import SkyCoord
from astropy.table import Table
import astropy.units as u
import numpy as np
import logging
import time
import random

logger = logging.getLogger(__name__)

from src.config import AppConfig
from src.tools.capture_sky.types import CelestialPosition, CelestialObject


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
    'Pl': 'Planet', 'Pl?': 'Planet Candidate', 'Com': 'Comet', 'As': 'Asteroid', 'Y*0': 'Young Stellar Object',
}


def _query_simbad_at_position(ra: float, dec: float, radius_arcsec: float, config: AppConfig, query_id: int) -> Optional[CelestialObject]:
    """
    Query SIMBAD for the closest object at a specific position.
    
    Args:
        ra: Right Ascension in degrees
        dec: Declination in degrees
        radius_arcsec: Search radius in arcseconds
        config: Application configuration
    
    Returns:
        CelestialObject if found, None otherwise.
    """
    try:
        coord = SkyCoord(ra=ra * u.deg, dec=dec * u.deg, frame='icrs')
        
        # Configure SIMBAD query with selected fields
        custom_simbad = Simbad()
        custom_simbad.add_votable_fields(
            'otype',       # Object type code (e.g., '*', 'G')
            'V',           # Visual magnitude
            'B',           # Blue magnitude (for B-V color index)
            'sp_type',     # Spectral type (e.g., 'G2V')
            'morph_type',  # Morphological type (for galaxies)
            'plx_value',   # Parallax (for distance calculation)
            'plx_value',   # Parallax (for distance calculation)
            'dim_majaxis', # Major axis angular size (arcminutes)
            'ids'          # All identifiers (to find common name)
        )
        custom_simbad.ROW_LIMIT = 5  # We only need the closest matches
        
        # Query with specified radius
        radius_arcsec = max(
            radius_arcsec,
            config.simbad_search_radius_arcsec
        )

        result = cast(Optional[Table], custom_simbad.query_region(
            coord, 
            radius=radius_arcsec * u.arcsec
        ))
        
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
                            obj_ra, obj_dec = float(ra_val), float(dec_val) # type: ignore
                        except (ValueError, TypeError):
                            # Try parsing as sexagesimal
                            try:
                                c = SkyCoord(str(ra_val), str(dec_val), unit=(u.hourangle, u.deg))
                                obj_ra, obj_dec = c.ra.deg, c.dec.deg # type: ignore
                            except:
                                continue
                        
                        # Calculate angular distance
                        obj_coord = SkyCoord(ra=obj_ra * u.deg, dec=obj_dec * u.deg, frame='icrs')
                        sep = coord.separation(obj_coord).arcsec
                        
                        if sep < min_distance: # type: ignore
                            min_distance = sep
                            closest_row = row
            except Exception:
                continue
        
        if closest_row is None:
            return None
        
        # Parse the closest object
        return _parse_simbad_row(closest_row, result.colnames, ra, dec, radius_arcsec)
        
    except Exception as e:
        # Query failed - return None silently
        return None


def _parse_simbad_row(row, colnames: List[str], query_ra: float, query_dec: float, query_radius_arcsec: float) -> CelestialObject:
    """
    Parse a SIMBAD result row into a CelestialObject.
    """
    # Get main identifier
    main_id = str(row['main_id']).strip()
    name = main_id

    # Try to find a common name (NAME identifier) from the IDs list
    if 'ids' in colnames and not np.ma.is_masked(row['ids']):
        # IDs are pipe-separated
        ids_list = str(row['ids']).split('|')
        for id_str in ids_list:
            id_str = id_str.strip()
            # Look for IDs starting with "NAME "
            if id_str.startswith('NAME '):
                # Use the name part (strip "NAME " prefix)
                name = id_str[5:].strip()
                break
    
    # Clean up name formatting (only if still using main_id or if needed)
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
                    obj_ra, obj_dec = c.ra.deg, c.dec.deg # type: ignore
                except:
                    pass
    
    # Get magnitudes
    mag = None
    mag_v = None
    mag_b = None
    
    if 'V' in colnames and not np.ma.is_masked(row['V']):
        mag_v = float(row['V'])
        mag = mag_v
    if 'B' in colnames and not np.ma.is_masked(row['B']):
        mag_b = float(row['B'])
        if mag is None:
            mag = mag_b
    
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
    
    # Get object angular size (dim_majaxis is in arcminutes, convert to arcseconds)
    object_radius_arcsec = None
    if 'dim_majaxis' in colnames and not np.ma.is_masked(row['dim_majaxis']):
        try:
            # dim_majaxis gives diameter in arcminutes, so radius = (diameter / 2) * 60 arcsec
            diameter_arcmin = float(row['dim_majaxis'])
            object_radius_arcsec = (diameter_arcmin / 2.0) * 60.0
        except (ValueError, TypeError):
            pass
    
    # Determine catalog category
    if name.startswith('M') and name[1:].strip().isdigit():
        catalog = 'Messier'
    elif name.startswith('NGC') or name.startswith('IC'):
        catalog = 'NGC/IC'
    elif '*' in otype or 'Star' in otype_description:
        catalog = 'Star'
    else:
        catalog = 'Deep Sky'
    
    return CelestialObject(
        name=name,
        catalog=catalog,
        position=CelestialPosition(
            ra=obj_ra if obj_ra is not None else query_ra, # type: ignore
            dec=obj_dec if obj_dec is not None else query_dec, # type: ignore
            radius_arcsec=object_radius_arcsec if object_radius_arcsec is not None else query_radius_arcsec
        ),
        alternative_names=alt_names if alt_names else None,
        object_type_description=otype_description if otype_description else None,
        magnitude_visual=mag_v,
        bv_color_index=bv_index,
        spectral_type=spectral_type,
        morphological_type=morph_type,
        distance_lightyears=distance_ly,
    )


def _worker_query_task(idx: int, pos: CelestialPosition, config: AppConfig) -> tuple[int, Optional[CelestialObject]]:
    """
    Worker function for parallel SIMBAD queries.
    Must be at module level for ProcessPoolExecutor pickling.
    """
    query_id = idx + 1
    
    result = _query_simbad_at_position(pos.ra, pos.dec, pos.radius_arcsec, config, query_id)
    return idx, result

def query_simbad_batch(
    config: AppConfig,
    positions: List[CelestialPosition],
    max_workers: int = 10,
    show_progress: bool = True,
) -> List[Optional[CelestialObject]]:
    """
    Query SIMBAD for multiple positions in parallel.
    
    Args:
        positions: List of CelestialPosition with ra, dec, and radius_arcsec
        max_workers: Maximum number of parallel queries
        show_progress: Whether to show tqdm progress bar
        config: Application configuration
    
    Returns:
        List of CelestialObject, one per position (None if no match)
    """
    from concurrent.futures import ProcessPoolExecutor, as_completed
    from tqdm import tqdm
    
    if not positions:
        return []
    
    # Create a mapping from index to position for ordered results
    results: List[Optional[CelestialObject]] = [None] * len(positions)
    
    # Cap workers to 6 to respect SIMBAD rate limits (6 queries/sec)
    actual_workers = min(max_workers, 6)
    
    # Run queries in parallel using ProcessPoolExecutor to bypass GIL
    with ProcessPoolExecutor(max_workers=actual_workers) as executor:
        futures = {
            executor.submit(_worker_query_task, i, pos, config): i 
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
            except Exception as e:
                logger.error(f"SIMBAD query failed: {e}")
                pass  # Keep None for failed queries
    
    return results
