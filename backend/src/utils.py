def ra_to_hms(ra_deg: float) -> str:
    """Convert RA from degrees to hours, minutes, seconds format."""
    ra_hours = ra_deg / 15.0
    h = int(ra_hours)
    m = int((ra_hours - h) * 60)
    s = ((ra_hours - h) * 60 - m) * 60
    return f"{h}h {m}m {s:.2f}s"


def dec_to_dms(dec_deg: float) -> str:
    """Convert DEC from degrees to degrees, minutes, seconds format."""
    sign = "+" if dec_deg >= 0 else "-"
    dec_abs = abs(dec_deg)
    d = int(dec_abs)
    m = int((dec_abs - d) * 60)
    s = ((dec_abs - d) * 60 - m) * 60
    return f"{sign}{d}° {m}' {s:.2f}\""
