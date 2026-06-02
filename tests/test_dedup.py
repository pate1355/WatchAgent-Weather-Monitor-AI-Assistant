from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest

from watchagent.cities import CITIES
from watchagent.config import Settings
from watchagent.poller.client import CurrentReading, OpenMeteoClient
from watchagent.poller.loop import Poller
from watchagent.storage.models import Base, Reading
from watchagent.storage.repo import Repository


@pytest.fixture
def poller_setup(settings, engine, session_factory):
    Base.metadata.create_all(engine)
    session = session_factory()
    repo = Repository(session)
    assert repo.count_readings() == 0

    obs_time = datetime(2026, 6, 1, 12, 0, tzinfo=timezone.utc)
    def make_reading(city_name: str) -> CurrentReading:
        return CurrentReading(
            city=city_name,
            observation_time=obs_time,
            observation_time_local="2026-06-01T12:00",
            temperature_2m=20.0,
            apparent_temperature=19.0,
            precipitation=0.0,
            wind_speed_10m=10.0,
            weather_code=0,
        )

    client = AsyncMock(spec=OpenMeteoClient)
    client.fetch_current = AsyncMock(side_effect=lambda c: make_reading(c.name))
    client.close = AsyncMock()

    poller = Poller(settings, client=client)

    with patch("watchagent.poller.loop.get_session_factory", return_value=session_factory):
        yield poller, session_factory, obs_time

    session.close()


def test_deduplication_same_timestamp_repo(db_session):
    repo = Repository(db_session)
    obs_time = datetime(2026, 6, 1, 12, 0, tzinfo=timezone.utc)
    for _ in range(2):
        repo.insert_reading(
            city="Ottawa",
            observation_time=obs_time,
            observation_time_local="2026-06-01T12:00",
            temperature_2m=20.0,
            apparent_temperature=19.0,
            precipitation=0.0,
            wind_speed_10m=10.0,
            weather_code=0,
        )
    repo.commit()
    assert repo.count_readings() == 1


@pytest.mark.asyncio
async def test_deduplication_same_timestamp_poller(poller_setup):
    poller, session_factory, _ = poller_setup
    await poller.poll_once()
    await poller.poll_once()

    session = session_factory()
    repo = Repository(session)
    assert repo.count_readings() == 3
    assert repo.count_readings() == len(CITIES)
    assert len(repo.list_readings(city="Ottawa")) == 1
    session.close()


@pytest.mark.asyncio
async def test_stores_reading_per_city_once(poller_setup):
    poller, session_factory, obs_time = poller_setup
    readings_by_city = {
        "Ottawa": CurrentReading(
            "Ottawa", obs_time, "2026-06-01T12:00", 20.0, 19.0, 0.0, 10.0, 0
        ),
        "Toronto": CurrentReading(
            "Toronto", obs_time, "2026-06-01T12:00", 22.0, 21.0, 0.0, 12.0, 1
        ),
        "Vancouver": CurrentReading(
            "Vancouver", obs_time, "2026-06-01T12:00", 18.0, 17.0, 0.0, 8.0, 2
        ),
    }

    async def fetch(city):
        return readings_by_city[city.name]

    poller.client.fetch_current = AsyncMock(side_effect=fetch)

    with patch("watchagent.poller.loop.get_session_factory", return_value=session_factory):
        await poller.poll_once()
        await poller.poll_once()

    session = session_factory()
    repo = Repository(session)
    assert repo.count_readings() == 3
    session.close()
