"""
Object visibility calculator tool.

Given an observer location, date, and list of celestial objects, computes
rise/set/transit times, maximum altitude, best observation window, and moon
separation for each target.
"""

from datetime import datetime, timezone
from typing import Optional

import astropy.units as u
from astropy.coordinates import EarthLocation, SkyCoord, get_body, AltAz
from astropy.time import Time
from astroplan import Observer, FixedTarget
from astroplan import (
    AltitudeConstraint,
    AtNightConstraint,
    is_observable,
)
import numpy as np
import logging

logger = logging.getLogger(__name__)


def _time_to_iso(t: Time) -> Optional[str]:
    """Convert an astropy Time to ISO-8601 UTC string, or None."""
    try:
        return t.utc.iso
    except Exception:
        return None


def _safe_event(func, *args, **kwargs) -> Optional[Time]:
    """Call an astroplan event function, returning None on failure."""
    try:
        result = func(*args, **kwargs)
        # astroplan returns masked values when the event doesn't occur
        if hasattr(result, "mask") and np.any(result.mask):
            return None
        return result
    except Exception:
        return None


def calculate_object_visibility(
    latitude: float,
    longitude: float,
    objects: list[dict],
    elevation_m: float = 0.0,
    date: str = "",
    min_altitude_deg: float = 20.0,
) -> dict:
    """
    Calculate visibility details for a list of celestial objects at a given
    observer location and date.

    For each object the tool returns rise/set/transit times, maximum altitude,
    the best observation window (when the object is above min_altitude during
    darkness), and the angular separation from the Moon.

    Args:
        latitude: Observer latitude in decimal degrees (positive = North).
        longitude: Observer longitude in decimal degrees (positive = East).
        objects: List of target objects. Each dict must contain:
            - name (str): Display name.
            - ra_deg (float): Right Ascension in decimal degrees (J2000).
            - dec_deg (float): Declination in decimal degrees (J2000).
        elevation_m: Observer elevation above sea level in metres (default 0).
        date: ISO date string (YYYY-MM-DD) for the observation night.
              Defaults to today if empty.
        min_altitude_deg: Minimum altitude in degrees for an object to be
            considered observable (default 20).

    Returns:
        A dictionary with:
        - success: bool
        - results: list of dicts, one per input object, each containing
          rise_time, set_time, transit_time, max_altitude_deg,
          best_observation_window (dict with start and end),
          moon_separation_deg, is_observable.
    """
    try:
        # --- Build observer ---------------------------------------------------
        location = EarthLocation(
            lat=latitude * u.deg,
            lon=longitude * u.deg,
            height=elevation_m * u.m,
        )
        observer = Observer(location=location)

        # Reference time: local midnight of the requested date
        if date:
            ref_date = datetime.fromisoformat(date).replace(tzinfo=timezone.utc)
        else:
            ref_date = datetime.now(timezone.utc)

        midnight = observer.midnight(Time(ref_date), which="next")

        # Darkness window (astronomical twilight)
        dark_start = _safe_event(
            observer.twilight_evening_astronomical, midnight, which="previous"
        )
        dark_end = _safe_event(
            observer.twilight_morning_astronomical, midnight, which="next"
        )

        # Moon position at midnight (for separation calc)
        moon_midnight = get_body("moon", midnight, location)

        # Observability constraints
        constraints = [
            AltitudeConstraint(min=min_altitude_deg * u.deg),
            AtNightConstraint.twilight_astronomical(),
        ]

        # --- Process each object ----------------------------------------------
        results: list[dict] = []

        for obj in objects:
            name = obj.get("name", "Unknown")
            try:
                ra = float(obj["ra_deg"])
                dec = float(obj["dec_deg"])
            except (KeyError, ValueError, TypeError) as exc:
                results.append({
                    "name": name,
                    "error": f"Invalid coordinates: {exc}",
                    "is_observable": False,
                })
                continue

            coord = SkyCoord(ra=ra * u.deg, dec=dec * u.deg, frame="icrs")
            target = FixedTarget(coord=coord, name=name)

            # Rise / set / transit
            rise = _safe_event(observer.target_rise_time, midnight, target, which="previous")
            if rise is None:
                rise = _safe_event(observer.target_rise_time, midnight, target, which="next")
            set_time = _safe_event(observer.target_set_time, midnight, target, which="next")
            transit = _safe_event(observer.target_meridian_transit_time, midnight, target, which="nearest")

            # Max altitude (at transit)
            if transit is not None:
                altaz_frame = AltAz(obstime=transit, location=location)
                alt_at_transit = coord.transform_to(altaz_frame).alt.deg
                max_alt = round(float(alt_at_transit), 1)
            else:
                max_alt = None

            # Moon separation
            moon_sep = round(float(coord.separation(moon_midnight).deg), 1)

            # Observability check using astroplan constraints
            try:
                observable = bool(
                    is_observable(constraints, observer, [target], time_range=[dark_start, dark_end])[0]
                ) if (dark_start is not None and dark_end is not None) else False
            except Exception:
                observable = False

            # Best observation window: find when the object is above
            # min_altitude during the darkness window
            best_start = None
            best_end = None

            if observable and dark_start is not None and dark_end is not None:
                try:
                    # Sample altitudes every 15 minutes during darkness
                    n_samples = int(((dark_end - dark_start).to_value(u.hour)) * 4) + 1
                    n_samples = max(n_samples, 2)
                    times = dark_start + np.linspace(0, 1, n_samples) * (dark_end - dark_start)

                    altaz_frames = AltAz(obstime=times, location=location)
                    alts = coord.transform_to(altaz_frames).alt.deg

                    above_mask = alts >= min_altitude_deg
                    if np.any(above_mask):
                        indices = np.where(above_mask)[0]
                        best_start = _time_to_iso(times[indices[0]])
                        best_end = _time_to_iso(times[indices[-1]])
                except Exception:
                    pass

            results.append({
                "name": name,
                "rise_time": _time_to_iso(rise) if rise is not None else None,
                "set_time": _time_to_iso(set_time) if set_time is not None else None,
                "transit_time": _time_to_iso(transit) if transit is not None else None,
                "max_altitude_deg": max_alt,
                "best_observation_window": {
                    "start": best_start,
                    "end": best_end,
                } if best_start else None,
                "moon_separation_deg": moon_sep,
                "is_observable": observable,
            })

        return {
            "success": True,
            "results": results,
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Visibility calculation failed: {str(e)}",
            "results": [],
        }
