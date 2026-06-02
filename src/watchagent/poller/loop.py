import asyncio
import logging

from watchagent.cities import CITIES
from watchagent.config import Settings
from watchagent.events.detector import EventDetector
from watchagent.poller.client import OpenMeteoClient
from watchagent.storage.database import get_session_factory
from watchagent.storage.repo import Repository

logger = logging.getLogger(__name__)


class Poller:
    def __init__(self, settings: Settings, client: OpenMeteoClient | None = None):
        self.settings = settings
        self.client = client or OpenMeteoClient(settings)
        self._task: asyncio.Task | None = None
        self._stop = asyncio.Event()

    async def start(self) -> None:
        if self._task is None:
            self._stop.clear()
            self._task = asyncio.create_task(self._run_loop())
            logger.info("Poller started", extra={"interval_seconds": self.settings.poll_interval_seconds})

    async def stop(self) -> None:
        self._stop.set()
        if self._task:
            await self._task
            self._task = None
        await self.client.close()
        logger.info("Poller stopped")

    async def _run_loop(self) -> None:
        while not self._stop.is_set():
            await self.poll_once()
            try:
                await asyncio.wait_for(
                    self._stop.wait(),
                    timeout=self.settings.poll_interval_seconds,
                )
            except asyncio.TimeoutError:
                pass

    async def poll_once(self) -> None:
        results = await asyncio.gather(
            *[self._poll_city(city) for city in CITIES],
            return_exceptions=True,
        )
        for city, result in zip(CITIES, results, strict=True):
            if isinstance(result, Exception):
                logger.warning(
                    "City poll failed",
                    extra={"city": city.name, "error": str(result)},
                )

    async def _poll_city(self, city) -> None:
        reading_data = await self.client.fetch_current(city)
        session = get_session_factory()()
        try:
            repo = Repository(session)
            reading = repo.insert_reading(
                city=reading_data.city,
                observation_time=reading_data.observation_time,
                observation_time_local=reading_data.observation_time_local,
                temperature_2m=reading_data.temperature_2m,
                apparent_temperature=reading_data.apparent_temperature,
                precipitation=reading_data.precipitation,
                wind_speed_10m=reading_data.wind_speed_10m,
                weather_code=reading_data.weather_code,
            )
            if reading:
                logger.info(
                    "Stored new reading",
                    extra={"city": city.name, "observation_time": str(reading.observation_time)},
                )
                detector = EventDetector(repo, self.settings)
                detector.evaluate_new_reading(reading)
                detector.evaluate_cross_city()
            repo.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
