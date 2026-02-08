"""
Observable-object catalog search tool.

Provides a curated catalog of ~110 Messier objects plus popular Caldwell/NGC
targets, and supplements results with live SIMBAD queries when a constellation
or specific object-type filter is requested.  Planets are computed on-the-fly
with ``astropy.coordinates.get_body``.
"""

from astropy.coordinates import get_body
from astropy.time import Time
import logging

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Curated catalog – Messier + selected Caldwell / NGC showpieces
# Each entry: (name, object_type, ra_deg, dec_deg, magnitude, constellation, description)
# Coordinates are J2000 epoch in decimal degrees.
# ---------------------------------------------------------------------------
_CURATED_CATALOG: list[tuple[str, str, float, float, float, str, str]] = [
    # --- Galaxies ---
    ("M31", "Galaxy", 10.6847, 41.2687, 3.4, "Andromeda", "Andromeda Galaxy – nearest large spiral galaxy, visible to the naked eye"),
    ("M33", "Galaxy", 23.4621, 30.6602, 5.7, "Triangulum", "Triangulum Galaxy – third-largest in the Local Group"),
    ("M51", "Galaxy", 202.4696, 47.1952, 8.4, "Canes Venatici", "Whirlpool Galaxy – classic face-on spiral with companion NGC 5195"),
    ("M81", "Galaxy", 148.8882, 69.0653, 6.9, "Ursa Major", "Bode's Galaxy – bright spiral galaxy paired with M82"),
    ("M82", "Galaxy", 148.9685, 69.6797, 8.4, "Ursa Major", "Cigar Galaxy – starburst galaxy with dramatic outflows"),
    ("M83", "Galaxy", 204.2538, -29.8657, 7.5, "Hydra", "Southern Pinwheel Galaxy – face-on barred spiral"),
    ("M87", "Galaxy", 187.7059, 12.3911, 8.6, "Virgo", "Virgo A – giant elliptical galaxy hosting a supermassive black hole"),
    ("M101", "Galaxy", 210.8024, 54.3490, 7.9, "Ursa Major", "Pinwheel Galaxy – grand-design face-on spiral"),
    ("M104", "Galaxy", 189.9976, -11.6231, 8.0, "Virgo", "Sombrero Galaxy – edge-on spiral with prominent dust lane"),
    ("M64", "Galaxy", 194.1827, 21.6828, 8.5, "Coma Berenices", "Black Eye Galaxy – spiral with a dramatic dark dust band"),
    ("M63", "Galaxy", 198.9554, 42.0293, 8.6, "Canes Venatici", "Sunflower Galaxy – flocculent spiral"),
    ("M66", "Galaxy", 170.0626, 12.9915, 8.9, "Leo", "Part of the Leo Triplet – distorted by gravitational interaction"),
    ("M65", "Galaxy", 169.7330, 13.0922, 9.3, "Leo", "Leo Triplet member – tilted spiral galaxy"),
    ("M106", "Galaxy", 184.7397, 47.3039, 8.4, "Canes Venatici", "Seyfert galaxy with anomalous spiral arms"),
    ("M74", "Galaxy", 24.1740, 15.7836, 9.4, "Pisces", "Phantom Galaxy – perfect face-on grand-design spiral"),
    ("M77", "Galaxy", 40.6696, -0.0133, 8.9, "Cetus", "Active Seyfert galaxy with bright nucleus"),
    ("NGC 253", "Galaxy", 11.888, -25.288, 7.2, "Sculptor", "Sculptor Galaxy – bright starburst galaxy"),
    ("NGC 4565", "Galaxy", 189.0866, 25.9877, 9.6, "Coma Berenices", "Needle Galaxy – spectacular edge-on spiral"),

    # --- Nebulae (emission, reflection, planetary) ---
    ("M42", "Nebula", 83.8221, -5.3911, 4.0, "Orion", "Orion Nebula – the brightest diffuse nebula, a stellar nursery"),
    ("M43", "Nebula", 83.8917, -5.2611, 9.0, "Orion", "De Mairan's Nebula – part of the Orion Nebula complex"),
    ("M1", "Supernova Remnant", 83.6331, 22.0145, 8.4, "Taurus", "Crab Nebula – remnant of the 1054 AD supernova, contains a pulsar"),
    ("M8", "Nebula", 270.9042, -24.3800, 6.0, "Sagittarius", "Lagoon Nebula – large emission nebula with embedded cluster"),
    ("M17", "Nebula", 275.1958, -16.1731, 6.0, "Sagittarius", "Omega / Swan Nebula – bright emission nebula"),
    ("M20", "Nebula", 270.6225, -23.0300, 6.3, "Sagittarius", "Trifid Nebula – emission, reflection, and dark nebula combined"),
    ("M16", "Nebula", 274.7000, -13.8067, 6.0, "Serpens", "Eagle Nebula – home of the Pillars of Creation"),
    ("M27", "Planetary Nebula", 299.9015, 22.7212, 7.5, "Vulpecula", "Dumbbell Nebula – bright and large planetary nebula"),
    ("M57", "Planetary Nebula", 283.3963, 33.0289, 8.8, "Lyra", "Ring Nebula – iconic planetary nebula with ring structure"),
    ("M76", "Planetary Nebula", 25.5821, 51.5754, 10.1, "Perseus", "Little Dumbbell Nebula – faint but beautiful bipolar nebula"),
    ("M97", "Planetary Nebula", 168.6986, 55.0192, 9.9, "Ursa Major", "Owl Nebula – round planetary nebula with owl-like 'eyes'"),
    ("NGC 7293", "Planetary Nebula", 337.4107, -20.8372, 7.6, "Aquarius", "Helix Nebula – nearest bright planetary nebula, the 'Eye of God'"),
    ("NGC 7000", "Nebula", 314.6800, 44.3200, 4.0, "Cygnus", "North America Nebula – large emission nebula shaped like North America"),
    ("NGC 2237", "Nebula", 97.9700, 5.0500, 9.0, "Monoceros", "Rosette Nebula – large circular emission nebula"),
    ("IC 1396", "Nebula", 324.7500, 57.5000, 3.5, "Cepheus", "Elephant's Trunk Nebula region – large emission nebula with dark globules"),
    ("NGC 6960", "Supernova Remnant", 312.1667, 30.7167, 7.0, "Cygnus", "Western Veil Nebula – delicate supernova remnant filaments"),
    ("NGC 6992", "Supernova Remnant", 313.3792, 31.7194, 7.0, "Cygnus", "Eastern Veil Nebula – bright arc of the Cygnus Loop"),

    # --- Open Clusters ---
    ("M45", "Open Cluster", 56.8711, 24.1050, 1.6, "Taurus", "Pleiades – the Seven Sisters, a stunning naked-eye cluster"),
    ("M44", "Open Cluster", 130.0250, 19.6691, 3.7, "Cancer", "Beehive Cluster / Praesepe – large bright open cluster"),
    ("M35", "Open Cluster", 92.2250, 24.3333, 5.3, "Gemini", "Rich open cluster with nearby faint NGC 2158"),
    ("M36", "Open Cluster", 84.0842, 34.1353, 6.3, "Auriga", "Pinwheel Cluster – young open cluster"),
    ("M37", "Open Cluster", 88.0708, 32.5511, 6.2, "Auriga", "Richest open cluster in Auriga"),
    ("M38", "Open Cluster", 82.1708, 35.8486, 7.4, "Auriga", "Starfish Cluster – open cluster with cross pattern"),
    ("M6", "Open Cluster", 265.0833, -32.2167, 4.2, "Scorpius", "Butterfly Cluster – bright naked-eye cluster"),
    ("M7", "Open Cluster", 268.4625, -34.7933, 3.3, "Scorpius", "Ptolemy Cluster – one of the brightest open clusters"),
    ("M11", "Open Cluster", 282.7667, -6.2667, 6.3, "Scutum", "Wild Duck Cluster – very rich, dense open cluster"),
    ("M34", "Open Cluster", 40.5125, 42.7611, 5.5, "Perseus", "Bright and easy open cluster"),
    ("M46", "Open Cluster", 115.4375, -14.8167, 6.1, "Puppis", "Rich open cluster with planetary nebula NGC 2438 superimposed"),
    ("M47", "Open Cluster", 114.1500, -14.4833, 4.2, "Puppis", "Bright scattered open cluster near M46"),
    ("M48", "Open Cluster", 123.4250, -5.8000, 5.5, "Hydra", "Large scattered open cluster"),
    ("M41", "Open Cluster", 101.5042, -20.7572, 4.5, "Canis Major", "Open cluster 4° south of Sirius"),
    ("M67", "Open Cluster", 132.8250, 11.8167, 6.1, "Cancer", "One of the oldest known open clusters"),
    ("M52", "Open Cluster", 351.2042, 61.5931, 5.0, "Cassiopeia", "Rich open cluster near the Bubble Nebula"),
    ("NGC 869", "Open Cluster", 34.7500, 57.1333, 5.3, "Perseus", "h Persei – western half of the Double Cluster"),
    ("NGC 884", "Open Cluster", 35.6000, 57.1500, 6.1, "Perseus", "Chi Persei – eastern half of the Double Cluster"),
    ("NGC 457", "Open Cluster", 19.8750, 58.2833, 6.4, "Cassiopeia", "Owl / E.T. Cluster – distinctive shape with bright stars"),
    ("M39", "Open Cluster", 322.3167, 48.4333, 4.6, "Cygnus", "Loose bright cluster visible in binoculars"),
    ("M29", "Open Cluster", 305.9750, 38.5000, 7.1, "Cygnus", "Small open cluster near Sadr in Cygnus"),
    ("M103", "Open Cluster", 23.3042, 60.6597, 7.4, "Cassiopeia", "Small fan-shaped open cluster"),

    # --- Globular Clusters ---
    ("M13", "Globular Cluster", 250.4233, 36.4611, 5.8, "Hercules", "Great Globular Cluster in Hercules – finest in the northern sky"),
    ("M3", "Globular Cluster", 205.5484, 28.3773, 6.2, "Canes Venatici", "Bright globular with over 500,000 stars"),
    ("M5", "Globular Cluster", 229.6384, 2.0810, 5.7, "Serpens", "One of the oldest and largest globular clusters"),
    ("M15", "Globular Cluster", 322.4930, 12.1670, 6.2, "Pegasus", "Dense globular cluster, possibly containing a black hole"),
    ("M22", "Globular Cluster", 279.0998, -23.9047, 5.1, "Sagittarius", "One of the brightest and nearest globular clusters"),
    ("M92", "Globular Cluster", 259.2808, 43.1361, 6.3, "Hercules", "Bright globular often overlooked in favour of M13"),
    ("M2", "Globular Cluster", 323.3626, -0.8233, 6.5, "Aquarius", "Rich globular cluster"),
    ("M4", "Globular Cluster", 245.8968, -26.5258, 5.6, "Scorpius", "Nearest globular cluster to Earth, near Antares"),
    ("M10", "Globular Cluster", 254.2879, -4.1003, 6.6, "Ophiuchus", "Bright globular cluster in Ophiuchus"),
    ("M12", "Globular Cluster", 251.8097, -1.9483, 6.7, "Ophiuchus", "Loose globular cluster near M10"),
    ("M53", "Globular Cluster", 198.2302, 18.1693, 7.6, "Coma Berenices", "Remote globular cluster"),
    ("M79", "Globular Cluster", 81.0462, -24.5244, 7.7, "Lepus", "Winter globular – unusual for being far from the galactic centre"),
    ("M55", "Globular Cluster", 294.9988, -30.9647, 6.3, "Sagittarius", "Large loose globular cluster"),
    ("M62", "Globular Cluster", 255.3033, -30.1136, 6.5, "Ophiuchus", "Dense irregular globular near the galactic centre"),
    ("M80", "Globular Cluster", 244.2600, -22.9750, 7.9, "Scorpius", "Dense globular between Antares and Beta Scorpii"),
    ("M19", "Globular Cluster", 255.6575, -26.2680, 6.8, "Ophiuchus", "One of the most oblate globular clusters"),
    ("M56", "Globular Cluster", 289.1483, 30.1842, 8.3, "Lyra", "Small globular between Albireo and Sulafat"),
    ("M71", "Globular Cluster", 298.4438, 18.7792, 8.2, "Sagitta", "Loose globular cluster resembling an open cluster"),
    ("M107", "Globular Cluster", 248.1333, -13.0533, 7.9, "Ophiuchus", "Loose globular with dark lanes"),
    ("47 Tuc", "Globular Cluster", 6.0236, -72.0813, 4.1, "Tucana", "Second brightest globular cluster – splendid southern target"),
    ("Omega Centauri", "Globular Cluster", 201.6970, -47.4797, 3.7, "Centaurus", "Largest and brightest globular cluster in the Milky Way"),

    # --- Double / multiple stars (notable showpieces) ---
    ("Albireo", "Double Star", 292.6804, 27.9597, 3.1, "Cygnus", "Beta Cygni – stunning gold-and-blue colour-contrast double star"),
    ("Mizar & Alcor", "Double Star", 200.9813, 54.9254, 2.3, "Ursa Major", "Famous naked-eye double in the Big Dipper handle"),

    # --- Caldwell / NGC highlights not already covered ---
    ("NGC 104", "Globular Cluster", 6.0236, -72.0813, 4.1, "Tucana", "47 Tucanae – magnificent southern globular"),
    ("C14", "Open Cluster + Nebula", 35.1000, 57.1333, 5.3, "Perseus", "Double Cluster – h and Chi Persei together"),
    ("NGC 2392", "Planetary Nebula", 112.2946, 20.9117, 9.2, "Gemini", "Eskimo Nebula – bright compact planetary nebula"),
    ("NGC 3242", "Planetary Nebula", 156.1833, -18.6381, 7.8, "Hydra", "Ghost of Jupiter – bright blue planetary nebula"),
    ("NGC 6826", "Planetary Nebula", 296.2004, 50.5256, 8.8, "Cygnus", "Blinking Planetary – appears to blink with averted vision"),
    ("NGC 6543", "Planetary Nebula", 269.6392, 66.6331, 8.1, "Draco", "Cat's Eye Nebula – complex planetary nebula"),
]


# Pre-built lookup for quick filtering
_CATALOG_BY_TYPE: dict[str, list[dict]] = {}
for _entry in _CURATED_CATALOG:
    _name, _otype, _ra, _dec, _mag, _con, _desc = _entry
    _obj = {
        "name": _name,
        "catalog": "Curated",
        "object_type": _otype,
        "ra_deg": _ra,
        "dec_deg": _dec,
        "magnitude": _mag,
        "constellation": _con,
        "description": _desc,
    }
    _CATALOG_BY_TYPE.setdefault(_otype, []).append(_obj)
    # Also add under a normalised key so "Nebula" matches "Supernova Remnant" etc.
    _normalised = _otype.split()[0]  # e.g. "Supernova" from "Supernova Remnant"
    if _normalised != _otype:
        _CATALOG_BY_TYPE.setdefault(_normalised, []).append(_obj)


# Planets that astropy can compute ephemerides for
_PLANET_NAMES = ["mercury", "venus", "mars", "jupiter", "saturn", "uranus", "neptune"]


def search_observable_objects(
    object_types: list[str] | None = None,
    max_magnitude: float = 10.0,
    constellation: str = "",
    include_planets: bool = True,
    date: str = "",
    limit: int = 30,
) -> dict:
    """
    Search for interesting celestial objects to observe.

    Returns objects from a curated catalog of Messier, Caldwell, and NGC
    showpieces, optionally filtered by type, constellation, and brightness.
    Planets for the requested date can be included automatically.

    Args:
        object_types: List of desired object types to include.
            Valid types: "Galaxy", "Nebula", "Planetary Nebula",
            "Supernova Remnant", "Open Cluster", "Globular Cluster",
            "Double Star". If None or empty, all types are returned.
        max_magnitude: Maximum (faintest) apparent magnitude to include
            (default 10.0). Lower = brighter; e.g. 6.0 for naked-eye objects,
            10.0 for small-telescope targets.
        constellation: If provided, only return objects in this constellation
            (case-insensitive match).
        include_planets: Whether to include solar-system planets (default True).
        date: ISO date string (YYYY-MM-DD) for planet positions.
              Defaults to today if empty.
        limit: Maximum number of objects to return (default 30).

    Returns:
        A dictionary with:
        - success: bool
        - objects: list of dicts, each with name, catalog, object_type,
          ra_deg, dec_deg, magnitude, constellation, description.
        - total_matched: total objects matching the filters before the limit.
    """
    try:
        results: list[dict] = []

        # --- Filter curated catalog -------------------------------------------
        constellation_filter = constellation.strip().lower() if constellation else ""

        if object_types:
            # Collect matching types (case-insensitive partial match)
            type_lower = [t.lower() for t in object_types]
            candidates: list[dict] = []
            for _otype, objs in _CATALOG_BY_TYPE.items():
                if any(tl in _otype.lower() for tl in type_lower):
                    candidates.extend(objs)
            # Deduplicate by name
            seen = set()
            deduped: list[dict] = []
            for obj in candidates:
                if obj["name"] not in seen:
                    seen.add(obj["name"])
                    deduped.append(obj)
            candidates = deduped
        else:
            candidates = []
            seen = set()
            for _otype, objs in _CATALOG_BY_TYPE.items():
                for obj in objs:
                    if obj["name"] not in seen:
                        seen.add(obj["name"])
                        candidates.append(obj)

        for obj in candidates:
            if obj["magnitude"] > max_magnitude:
                continue
            if constellation_filter and obj["constellation"].lower() != constellation_filter:
                continue
            results.append(obj)

        # Sort by magnitude (brightest first)
        results.sort(key=lambda o: o["magnitude"])

        # --- Planets -----------------------------------------------------------
        if include_planets:
            try:
                if date:
                    from datetime import datetime as dt, timezone as tz
                    obs_time = Time(dt.fromisoformat(date).replace(tzinfo=tz.utc))
                else:
                    obs_time = Time.now()

                for pname in _PLANET_NAMES:
                    try:
                        body = get_body(pname, obs_time)
                        results.append({
                            "name": pname.capitalize(),
                            "catalog": "Solar System",
                            "object_type": "Planet",
                            "ra_deg": round(body.ra.deg, 4),
                            "dec_deg": round(body.dec.deg, 4),
                            "magnitude": None,
                            "constellation": "",
                            "description": f"Planet {pname.capitalize()} – position computed for {obs_time.iso[:10]}",
                        })
                    except Exception:
                        continue
            except Exception as exc:
                logger.warning("Planet computation failed: %s", exc)

        total_matched = len(results)
        results = results[:limit]

        return {
            "success": True,
            "objects": results,
            "total_matched": total_matched,
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Catalog search failed: {str(e)}",
            "objects": [],
            "total_matched": 0,
        }
