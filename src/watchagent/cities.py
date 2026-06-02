from dataclasses import dataclass


@dataclass(frozen=True)
class City:
    name: str
    latitude: float
    longitude: float


CITIES: tuple[City, ...] = (
    City("Ottawa", 45.42, -75.69),
    City("Toronto", 43.70, -79.42),
    City("Vancouver", 49.25, -123.12),
)

CITY_NAMES = frozenset(c.name for c in CITIES)
