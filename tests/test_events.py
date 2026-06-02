from datetime import datetime, timedelta, timezone

import pytest

from watchagent.config import Settings
from watchagent.events.detector import EventDetector
from watchagent.storage.models import Reading
from watchagent.storage.repo import Repository


def _reading(
    city: str,
    obs: datetime,
    temp: float,
    precip: float = 0.0,
    wind: float = 10.0,
    code: int = 0,
    rid: int | None = None,
) -> Reading:
    r = Reading(
        city=city,
        observation_time=obs,
        temperature_2m=temp,
        apparent_temperature=temp - 1,
        precipitation=precip,
        wind_speed_10m=wind,
        weather_code=code,
    )
    if rid is not None:
        r.id = rid
    return r


@pytest.fixture
def repo(db_session):
    return Repository(db_session)


@pytest.fixture
def detector(repo):
    settings = Settings(
        database_url="sqlite:///:memory:",
        rapid_temp_delta_c=4.0,
        heavy_precipitation_mm=5.0,
        high_wind_kmh=50.0,
        regional_contrast_delta_c=15.0,
        event_cooldown_minutes=60,
        heat_threshold_ottawa=32.0,
        cold_threshold_ottawa=-25.0,
    )
    return EventDetector(repo, settings)


def _insert(repo: Repository, reading: Reading) -> Reading:
    local = reading.observation_time.strftime("%Y-%m-%dT%H:%M")
    stored = repo.insert_reading(
        city=reading.city,
        observation_time=reading.observation_time,
        observation_time_local=local,
        temperature_2m=reading.temperature_2m,
        apparent_temperature=reading.apparent_temperature,
        precipitation=reading.precipitation,
        wind_speed_10m=reading.wind_speed_10m,
        weather_code=reading.weather_code,
    )
    assert stored is not None
    repo.commit()
    return stored


def test_rapid_temp_change_fires(repo, detector):
    t0 = datetime(2026, 6, 1, 10, 0, tzinfo=timezone.utc)
    t1 = datetime(2026, 6, 1, 11, 0, tzinfo=timezone.utc)
    _insert(repo, _reading("Ottawa", t0, 10.0, code=0))
    r2 = _insert(repo, _reading("Ottawa", t1, 15.0, code=0))

    events = detector.evaluate_new_reading(r2)
    types = [e["event_type"] for e in events]
    assert "rapid_temp_change" in types


def test_rapid_temp_change_not_on_first_reading(repo, detector):
    t0 = datetime(2026, 6, 1, 10, 0, tzinfo=timezone.utc)
    r1 = _insert(repo, _reading("Ottawa", t0, 10.0))

    events = detector.evaluate_new_reading(r1)
    assert not any(e["event_type"] == "rapid_temp_change" for e in events)


def test_small_temp_change_does_not_fire(repo, detector):
    t0 = datetime(2026, 6, 1, 10, 0, tzinfo=timezone.utc)
    t1 = datetime(2026, 6, 1, 11, 0, tzinfo=timezone.utc)
    _insert(repo, _reading("Ottawa", t0, 10.0))
    r2 = _insert(repo, _reading("Ottawa", t1, 12.0))

    events = detector.evaluate_new_reading(r2)
    assert not any(e["event_type"] == "rapid_temp_change" for e in events)


def test_extreme_heat_fires(repo, detector):
    t0 = datetime(2026, 7, 1, 14, 0, tzinfo=timezone.utc)
    r = _insert(repo, _reading("Ottawa", t0, 35.0))

    events = detector.evaluate_new_reading(r)
    assert any(e["event_type"] == "extreme_heat" for e in events)


def test_extreme_cold_fires(repo, detector):
    t0 = datetime(2026, 1, 1, 6, 0, tzinfo=timezone.utc)
    r = _insert(repo, _reading("Ottawa", t0, -30.0))

    events = detector.evaluate_new_reading(r)
    assert any(e["event_type"] == "extreme_cold" for e in events)


def test_heavy_precipitation_fires(repo, detector):
    t0 = datetime(2026, 6, 1, 12, 0, tzinfo=timezone.utc)
    r = _insert(repo, _reading("Ottawa", t0, 15.0, precip=8.0))

    events = detector.evaluate_new_reading(r)
    assert any(e["event_type"] == "heavy_precipitation" for e in events)


def test_high_wind_fires(repo, detector):
    t0 = datetime(2026, 6, 1, 12, 0, tzinfo=timezone.utc)
    r = _insert(repo, _reading("Ottawa", t0, 15.0, wind=55.0))

    events = detector.evaluate_new_reading(r)
    assert any(e["event_type"] == "high_wind" for e in events)


def test_conditions_shift_fires(repo, detector):
    t0 = datetime(2026, 6, 1, 10, 0, tzinfo=timezone.utc)
    t1 = datetime(2026, 6, 1, 11, 0, tzinfo=timezone.utc)
    _insert(repo, _reading("Ottawa", t0, 15.0, code=0))
    r2 = _insert(repo, _reading("Ottawa", t1, 14.0, code=61))

    events = detector.evaluate_new_reading(r2)
    assert any(e["event_type"] == "conditions_shift" for e in events)


def test_blizzard_warning_fires(repo, detector):
    t0 = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
    r = _insert(repo, _reading("Ottawa", t0, -10.0, precip=2.0, wind=45.0))

    events = detector.evaluate_new_reading(r)
    assert any(e["event_type"] == "blizzard_warning" for e in events)


def test_regional_contrast_fires(repo, detector):
    now = datetime.now(timezone.utc)
    _insert(repo, _reading("Ottawa", now, 30.0))
    _insert(repo, _reading("Vancouver", now, 10.0))
    _insert(repo, _reading("Toronto", now, 20.0))

    events = detector.evaluate_cross_city()
    assert any(e["event_type"] == "regional_contrast" for e in events)


def test_cooldown_suppresses_duplicate(repo, detector):
    t0 = datetime(2026, 6, 1, 10, 0, tzinfo=timezone.utc)
    r1 = _insert(repo, _reading("Ottawa", t0, 35.0))
    first = detector.evaluate_new_reading(r1)
    repo.commit()
    assert any(e["event_type"] == "extreme_heat" for e in first)

    t1 = datetime(2026, 6, 1, 11, 0, tzinfo=timezone.utc)
    r2 = _insert(repo, _reading("Ottawa", t1, 36.0))
    second = detector.evaluate_new_reading(r2)
    assert not any(e["event_type"] == "extreme_heat" for e in second)
