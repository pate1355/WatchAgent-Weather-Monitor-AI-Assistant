import logging
from datetime import datetime, timedelta, timezone

from watchagent.config import Settings, get_cold_threshold, get_heat_threshold
from watchagent.events.wmo import weather_category
from watchagent.storage.models import Reading
from watchagent.storage.repo import Repository

logger = logging.getLogger(__name__)


class EventDetector:
    def __init__(self, repo: Repository, settings: Settings):
        self.repo = repo
        self.settings = settings

    def evaluate_new_reading(self, reading: Reading) -> list[dict]:
        events: list[dict] = []
        events.extend(self._check_rapid_temp_change(reading))
        events.extend(self._check_extreme_temperature(reading))
        events.extend(self._check_heavy_precipitation(reading))
        events.extend(self._check_high_wind(reading))
        events.extend(self._check_conditions_shift(reading))
        events.extend(self._check_blizzard_warning(reading))
        self._persist_events(events)
        return events

    def evaluate_cross_city(self) -> list[dict]:
        events: list[dict] = []
        events.extend(self._check_regional_contrast())
        self._persist_events(events)
        return events

    def _persist_events(self, events: list[dict]) -> None:
        for ev in events:
            self.repo.insert_event(**ev)
            logger.info(
                "Notable event detected",
                extra={"city": ev.get("city"), "event_type": ev["event_type"]},
            )

    def _on_cooldown(
        self, city: str | None, event_type: str, reference_time: datetime
    ) -> bool:
        since = reference_time - timedelta(minutes=self.settings.event_cooldown_minutes)
        return self.repo.has_recent_event(city, event_type, since)

    def _check_rapid_temp_change(self, reading: Reading) -> list[dict]:
        if self._on_cooldown(reading.city, "rapid_temp_change", reading.observation_time):
            return []
        previous = self.repo.get_previous_reading(reading.city, reading.observation_time)
        if not previous:
            return []
        delta = reading.temperature_2m - previous.temperature_2m
        if abs(delta) < self.settings.rapid_temp_delta_c:
            return []
        direction = "rose" if delta > 0 else "fell"
        return [
            {
                "city": reading.city,
                "occurred_at": reading.observation_time,
                "event_type": "rapid_temp_change",
                "title": f"Rapid temperature change in {reading.city}",
                "description": (
                    f"Temperature {direction} by {abs(delta):.1f}°C "
                    f"({previous.temperature_2m:.1f}°C → {reading.temperature_2m:.1f}°C)."
                ),
                "reason": (
                    f"Change of {abs(delta):.1f}°C exceeds threshold of "
                    f"{self.settings.rapid_temp_delta_c}°C versus the previous stored reading."
                ),
                "metadata": {
                    "previous_temperature": previous.temperature_2m,
                    "current_temperature": reading.temperature_2m,
                    "delta_c": delta,
                    "threshold_c": self.settings.rapid_temp_delta_c,
                },
                "reading_id": reading.id,
            }
        ]

    def _check_extreme_temperature(self, reading: Reading) -> list[dict]:
        events: list[dict] = []
        heat_limit = get_heat_threshold(reading.city, self.settings)
        cold_limit = get_cold_threshold(reading.city, self.settings)
        temp = reading.temperature_2m

        if temp >= heat_limit and not self._on_cooldown(
            reading.city, "extreme_heat", reading.observation_time
        ):
            events.append(
                {
                    "city": reading.city,
                    "occurred_at": reading.observation_time,
                    "event_type": "extreme_heat",
                    "title": f"Extreme heat in {reading.city}",
                    "description": f"Temperature reached {temp:.1f}°C (threshold {heat_limit}°C).",
                    "reason": (
                        f"{reading.city} heat threshold is {heat_limit}°C; "
                        "coastal and inland climates differ."
                    ),
                    "metadata": {
                        "temperature": temp,
                        "threshold": heat_limit,
                    },
                    "reading_id": reading.id,
                }
            )

        if temp <= cold_limit and not self._on_cooldown(
            reading.city, "extreme_cold", reading.observation_time
        ):
            events.append(
                {
                    "city": reading.city,
                    "occurred_at": reading.observation_time,
                    "event_type": "extreme_cold",
                    "title": f"Extreme cold in {reading.city}",
                    "description": f"Temperature dropped to {temp:.1f}°C (threshold {cold_limit}°C).",
                    "reason": (
                        f"{reading.city} cold threshold is {cold_limit}°C; "
                        "winter severity varies by region."
                    ),
                    "metadata": {
                        "temperature": temp,
                        "threshold": cold_limit,
                    },
                    "reading_id": reading.id,
                }
            )
        return events

    def _check_heavy_precipitation(self, reading: Reading) -> list[dict]:
        if self._on_cooldown(reading.city, "heavy_precipitation", reading.observation_time):
            return []
        if reading.precipitation < self.settings.heavy_precipitation_mm:
            return []
        return [
            {
                "city": reading.city,
                "occurred_at": reading.observation_time,
                "event_type": "heavy_precipitation",
                "title": f"Heavy precipitation in {reading.city}",
                "description": (
                    f"Precipitation in the preceding hour: {reading.precipitation:.1f} mm."
                ),
                "reason": (
                    f"Precipitation ≥ {self.settings.heavy_precipitation_mm} mm/h "
                    "indicates significant rainfall or snowfall intensity."
                ),
                "metadata": {
                    "precipitation_mm": reading.precipitation,
                    "threshold_mm": self.settings.heavy_precipitation_mm,
                },
                "reading_id": reading.id,
            }
        ]

    def _check_high_wind(self, reading: Reading) -> list[dict]:
        if self._on_cooldown(reading.city, "high_wind", reading.observation_time):
            return []
        if reading.wind_speed_10m < self.settings.high_wind_kmh:
            return []
        return [
            {
                "city": reading.city,
                "occurred_at": reading.observation_time,
                "event_type": "high_wind",
                "title": f"High wind in {reading.city}",
                "description": f"Wind speed {reading.wind_speed_10m:.1f} km/h.",
                "reason": (
                    f"Wind speed exceeds {self.settings.high_wind_kmh} km/h — "
                    "a separate signal from temperature-based alerts."
                ),
                "metadata": {
                    "wind_speed_kmh": reading.wind_speed_10m,
                    "threshold_kmh": self.settings.high_wind_kmh,
                },
                "reading_id": reading.id,
            }
        ]

    def _check_conditions_shift(self, reading: Reading) -> list[dict]:
        if self._on_cooldown(reading.city, "conditions_shift", reading.observation_time):
            return []
        previous = self.repo.get_previous_reading(reading.city, reading.observation_time)
        if not previous:
            return []
        prev_cat = weather_category(previous.weather_code)
        curr_cat = weather_category(reading.weather_code)
        if prev_cat == curr_cat:
            return []
        return [
            {
                "city": reading.city,
                "occurred_at": reading.observation_time,
                "event_type": "conditions_shift",
                "title": f"Weather conditions shifted in {reading.city}",
                "description": (
                    f"Category changed from {prev_cat} (code {previous.weather_code}) "
                    f"to {curr_cat} (code {reading.weather_code})."
                ),
                "reason": "WMO weather code category changed between consecutive readings.",
                "metadata": {
                    "previous_category": prev_cat,
                    "current_category": curr_cat,
                    "previous_code": previous.weather_code,
                    "current_code": reading.weather_code,
                },
                "reading_id": reading.id,
            }
        ]

    def _check_blizzard_warning(self, reading: Reading) -> list[dict]:
        if self._on_cooldown(reading.city, "blizzard_warning", reading.observation_time):
            return []
        
        # Blizzard conditions: temp <= -5°C, wind >= 40 km/h, and some precipitation
        if reading.temperature_2m <= -5.0 and reading.wind_speed_10m >= 40.0 and reading.precipitation > 0:
            return [
                {
                    "city": reading.city,
                    "occurred_at": reading.observation_time,
                    "event_type": "blizzard_warning",
                    "title": f"Blizzard Warning in {reading.city}",
                    "description": f"Compound event: Temp {reading.temperature_2m:.1f}°C, Wind {reading.wind_speed_10m:.1f} km/h, Precip {reading.precipitation:.1f} mm.",
                    "reason": "Severe winter conditions detected: Temperature ≤ -5°C, Wind ≥ 40 km/h, and active precipitation.",
                    "metadata": {
                        "temperature": reading.temperature_2m,
                        "wind_speed_kmh": reading.wind_speed_10m,
                        "precipitation_mm": reading.precipitation,
                    },
                    "reading_id": reading.id,
                }
            ]
        return []

    def _check_regional_contrast(self) -> list[dict]:
        latest = self.repo.get_latest_readings_all_cities()
        ottawa = latest.get("Ottawa")
        vancouver = latest.get("Vancouver")
        if not ottawa or not vancouver:
            return []

        max_age = timedelta(hours=self.settings.regional_contrast_max_age_hours)
        now = datetime.now(timezone.utc)
        for r in (ottawa, vancouver):
            obs = r.observation_time
            if obs.tzinfo is None:
                obs = obs.replace(tzinfo=timezone.utc)
            if now - obs > max_age:
                return []

        delta = abs(ottawa.temperature_2m - vancouver.temperature_2m)
        if delta < self.settings.regional_contrast_delta_c:
            return []

        ref_time = max(ottawa.observation_time, vancouver.observation_time)
        if self._on_cooldown(None, "regional_contrast", ref_time):
            return []

        return [
            {
                "city": None,
                "occurred_at": max(ottawa.observation_time, vancouver.observation_time),
                "event_type": "regional_contrast",
                "title": "Large temperature contrast: Ottawa vs Vancouver",
                "description": (
                    f"Ottawa {ottawa.temperature_2m:.1f}°C vs "
                    f"Vancouver {vancouver.temperature_2m:.1f}°C (Δ {delta:.1f}°C)."
                ),
                "reason": (
                    f"Cross-city temperature gap ≥ {self.settings.regional_contrast_delta_c}°C "
                    "with both readings fresh within "
                    f"{self.settings.regional_contrast_max_age_hours} hours."
                ),
                "metadata": {
                    "ottawa_temperature": ottawa.temperature_2m,
                    "vancouver_temperature": vancouver.temperature_2m,
                    "delta_c": delta,
                    "threshold_c": self.settings.regional_contrast_delta_c,
                },
                "reading_id": None,
            }
        ]
