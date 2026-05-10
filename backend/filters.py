import re

# Matches PT4M30S, P1DT2H3M4S, P0D (active live stream), PT0S, etc.
_ISO_PATTERN = re.compile(
    r"^P(?:(\d+)D)?(?:T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?)?$"
)
_MIN_DURATION_SECONDS = 180


def iso8601_to_seconds(duration: str) -> int:
    """Convert an ISO 8601 duration string to total seconds.

    Raises ValueError for strings that don't match the expected pattern.
    """
    m = _ISO_PATTERN.match(duration)
    if not m:
        raise ValueError(f"Unrecognised ISO 8601 duration: {duration!r}")
    days, hours, minutes, seconds = (int(g or 0) for g in m.groups())
    return days * 86_400 + hours * 3_600 + minutes * 60 + seconds


def is_allowed(title: str, duration_seconds: int) -> bool:
    """Return True only if the video passes all business-rule filters.

    Rules (CLAUDE.md):
    - Duration must be >= 3 minutes (180 s)
    - Title must not contain '#shorts' (case-insensitive)
    """
    if duration_seconds < _MIN_DURATION_SECONDS:
        return False
    if "#shorts" in title.lower():
        return False
    return True
