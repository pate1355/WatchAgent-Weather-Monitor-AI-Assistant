import logging
from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

import httpx

from watchagent.cities import City
from watchagent.config import Settings

logger = logging.getLogger(__name__)

CURRENT_PARAMS = (
    "temperature_2m,apparent_temperature,precipitation,wind_speed_10m,weather_code"
)


@dataclass(frozen=True)
class CurrentReading:
    city: str
    observation_time: datetime
    observation_time_local: str
    temperature_2m: float
    apparent_temperature: float
    precipitation: float
    wind_speed_10m: float
    weather_code: int


class OpenMeteoClient:
    def __init__(self, settings: Settings, http_client: httpx.AsyncClient | None = None):
        self.settings = settings
        self._client = http_client
        self._owns_client = http_client is None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client

    async def close(self) -> None:
        if self._owns_client and self._client is not None:
            await self._client.aclose()
            self._client = None

    async def fetch_current(self, city: City) -> CurrentReading:
        client = await self._get_client()
        params = {
            "latitude": city.latitude,
            "longitude": city.longitude,
            "current": CURRENT_PARAMS,
            "wind_speed_unit": "kmh",
            "timezone": "auto",
        }
        last_error: Exception | None = None
        for attempt in range(1, self.settings.poller_max_retries + 1):
            try:
                response = await client.get(self.settings.open_meteo_base_url, params=params)
                if response.status_code != 200:
                    logger.warning(
                        "Open-Meteo fetch failed",
                        extra={
                            "city": city.name,
                            "http_status": response.status_code,
                            "retry_count": attempt,
                        },
                    )
                    last_error = httpx.HTTPStatusError(
                        "bad status", request=response.request, response=response
                    )
                else:
                    return self._parse_response(city.name, response.json())
            except httpx.HTTPError as exc:
                status = getattr(getattr(exc, "response", None), "status_code", None)
                logger.warning(
                    "Open-Meteo fetch failed",
                    extra={
                        "city": city.name,
                        "http_status": status,
                        "retry_count": attempt,
                    },
                )
                last_error = exc
            if attempt < self.settings.poller_max_retries:
                import asyncio

                delay = self.settings.poller_retry_base_seconds * (2 ** (attempt - 1))
                await asyncio.sleep(delay)
        raise RuntimeError(f"Failed to fetch weather for {city.name}") from last_error

    @staticmethod
    def _parse_response(city: str, data: dict) -> CurrentReading:
        current = data["current"]
        time_str = current["time"]
        obs_time = OpenMeteoClient._parse_observation_time(
            time_str, data.get("timezone", "UTC")
        )
        return CurrentReading(
            city=city,
            observation_time=obs_time,
            observation_time_local=time_str,
            temperature_2m=float(current["temperature_2m"]),
            apparent_temperature=float(current["apparent_temperature"]),
            precipitation=float(current["precipitation"]),
            wind_speed_10m=float(current["wind_speed_10m"]),
            weather_code=int(current["weather_code"]),
        )

    @staticmethod
    def _parse_observation_time(time_str: str, tz_name: str) -> datetime:
        """Open-Meteo returns current.time in the location timezone when timezone=auto."""
        if time_str.endswith("Z"):
            return datetime.fromisoformat(time_str.replace("Z", "+00:00"))
        if "+" in time_str[10:] or time_str.count("-") > 2:
            return datetime.fromisoformat(time_str)
        naive = datetime.fromisoformat(time_str)
        return naive.replace(tzinfo=ZoneInfo(tz_name))
