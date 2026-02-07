import os
from dataclasses import dataclass
from typing import Optional
import dotenv

@dataclass
class AppConfig:
    """Configuration for the image analysis tool."""
    astrometry_api_key: str
    plate_solving_timeout: int
    plate_solving_use_cache: bool
    webcam_index: int
    object_detector: str
    max_query_objects: int
    logs_dir: str
    verbose: bool
    simbad_search_radius_arcsec:int
    astrometry_api_url: str
    storage_dir: str
    
def get_config_from_env() -> AppConfig:
    dotenv.load_dotenv()

    astrometry_api_key = os.environ.get("ASTROMETRY_API_KEY")
    if astrometry_api_key is None:
        raise ValueError("ASTROMETRY_API_KEY environment variable is not set")

    """Get configuration from environment variables."""
    return AppConfig(
        astrometry_api_key=astrometry_api_key,
        plate_solving_timeout=int(os.environ.get("PLATE_SOLVING_TIMEOUT", "30")),
        plate_solving_use_cache=os.environ.get("PLATE_SOLVING_USE_CACHE", "False") == "true",
        webcam_index=int(os.environ.get("WEBCAM_INDEX", "0")),
        object_detector=os.environ.get("OBJECT_DETECTOR", "contrast_detector"),
        max_query_objects=int(os.environ.get("MAX_QUERY_OBJECTS", "10")),
        logs_dir=os.environ.get("LOGS_DIR", "logs"),
        verbose=os.environ.get("VERBOSE", "True") == "True",
        simbad_search_radius_arcsec=int(os.environ.get("SIMBAD_SEARCH_RADIUS", "10")),
        astrometry_api_url=os.environ.get("ASTROMETRY_API_URL", "http://ec2-3-145-73-178.us-east-2.compute.amazonaws.com/solve"),
        storage_dir=os.environ.get("STORAGE_DIR", "/mnt/data"),
    )