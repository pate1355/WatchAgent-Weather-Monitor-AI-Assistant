from datetime import datetime
from zoneinfo import ZoneInfo

CITY_TIMEZONES: dict[str, str] = {
    "Ottawa": "America/Toronto",
    "Toronto": "America/Toronto",
    "Vancouver": "America/Vancouver",
}


def local_iso_from_utc(dt: datetime, city: str) -> str:
    """Rebuild Open-Meteo-style local time (no offset) from a UTC-aware instant."""
    tz = ZoneInfo(CITY_TIMEZONES.get(city, "UTC"))
    if dt.tzinfo is None:
        from datetime import timezone

        dt = dt.replace(tzinfo=timezone.utc)
    local = dt.astimezone(tz)
    return local.strftime("%Y-%m-%dT%H:%M")
