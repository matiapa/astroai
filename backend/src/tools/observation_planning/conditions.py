"""
Observation conditions tool.

Computes sky conditions for a given observer location and date:
sunset/sunrise, astronomical twilight, moon phase, and darkness window.
"""

from datetime import datetime, timezone
from typing import Optional

import astropy.units as u
from astropy.coordinates import EarthLocation, AltAz, get_body
from astropy.time import Time
from astroplan import Observer


def _time_to_iso(t: Time) -> Optional[str]:
    """Convert an astropy Time to an ISO-8601 UTC string, or None."""
    try:
        return t.utc.iso
    except Exception:
        return None


def get_observation_conditions(
    latitude: float,
    longitude: float,
    elevation_m: float = 0.0,
    date: str = "",
) -> dict:
    """
    Compute sky conditions for a given observer location and date.

    Use this tool to determine the darkness window, moon interference, and
    overall observing conditions for a specific night.

    Args:
        latitude: Observer latitude in decimal degrees (positive = North).
        longitude: Observer longitude in decimal degrees (positive = East).
        elevation_m: Observer elevation above sea level in metres (default 0).
        date: ISO date string (YYYY-MM-DD) for the observation night.
              If empty, defaults to today's date (UTC).

    Returns:
        A dictionary with the following keys:
        - sunset, sunrise: UTC ISO timestamps of sunset and sunrise.
        - astronomical_twilight_start: UTC time when the sky becomes fully dark
          (sun 18° below horizon).
        - astronomical_twilight_end: UTC time when dawn begins (sun rises to 18°
          below horizon).
        - total_dark_hours: Number of hours of full astronomical darkness.
        - moon_phase_illumination: Moon illumination fraction (0.0 = new, 1.0 = full).
        - moon_rise, moon_set: UTC ISO timestamps of moonrise and moonset closest
          to the observation midnight.
        - moon_altitude_at_midnight: Moon altitude in degrees at local midnight.
    """
    try:
        # --- Build observer ---------------------------------------------------
        location = EarthLocation(
            lat=latitude * u.deg,
            lon=longitude * u.deg,
            height=elevation_m * u.m,
        )
        observer = Observer(location=location)

        # --- Reference time: local midnight of the requested date -------------
        if date:
            ref_date = datetime.fromisoformat(date).replace(tzinfo=timezone.utc)
        else:
            ref_date = datetime.now(timezone.utc)

        midnight = observer.midnight(Time(ref_date), which="next")

        # --- Sun events -------------------------------------------------------
        sunset = observer.sun_set_time(midnight, which="previous")
        sunrise = observer.sun_rise_time(midnight, which="next")
        astro_twilight_start = observer.twilight_evening_astronomical(
            midnight, which="previous"
        )
        astro_twilight_end = observer.twilight_morning_astronomical(
            midnight, which="next"
        )

        # Total dark hours
        try:
            dark_hours = (astro_twilight_end - astro_twilight_start).to_value(u.hour)
        except Exception:
            dark_hours = None

        # --- Moon data --------------------------------------------------------
        moon_illumination = observer.moon_illumination(midnight)

        try:
            moon_rise = observer.moon_rise_time(midnight, which="nearest")
        except Exception:
            moon_rise = None

        try:
            moon_set = observer.moon_set_time(midnight, which="nearest")
        except Exception:
            moon_set = None

        # Moon altitude at midnight
        altaz_frame = AltAz(obstime=midnight, location=location)
        moon_coords = get_body("moon", midnight, location)
        moon_altaz = moon_coords.transform_to(altaz_frame)
        moon_alt_midnight = round(moon_altaz.alt.deg, 1)

        return {
            "success": True,
            "sunset": _time_to_iso(sunset),
            "sunrise": _time_to_iso(sunrise),
            "astronomical_twilight_start": _time_to_iso(astro_twilight_start),
            "astronomical_twilight_end": _time_to_iso(astro_twilight_end),
            "total_dark_hours": round(dark_hours, 1) if dark_hours else None,
            "moon_phase_illumination": round(moon_illumination, 2),
            "moon_rise": _time_to_iso(moon_rise) if moon_rise is not None else None,
            "moon_set": _time_to_iso(moon_set) if moon_set is not None else None,
            "moon_altitude_at_midnight": moon_alt_midnight,
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to compute observation conditions: {str(e)}",
        }
