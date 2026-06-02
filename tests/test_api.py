from datetime import datetime, timezone

from watchagent.storage.repo import Repository


def _seed(repo: Repository) -> None:
    obs = datetime(2026, 6, 1, 12, 0, tzinfo=timezone.utc)
    reading = repo.insert_reading(
        city="Ottawa",
        observation_time=obs,
        observation_time_local="2026-06-01T12:00",
        temperature_2m=22.0,
        apparent_temperature=21.0,
        precipitation=0.0,
        wind_speed_10m=15.0,
        weather_code=1,
    )
    repo.insert_event(
        city="Ottawa",
        occurred_at=obs,
        event_type="extreme_heat",
        title="Test event",
        description="Hot day",
        reason="Testing",
        metadata={"temperature": 22.0},
        reading_id=reading.id if reading else None,
    )
    repo.commit()


def test_health_endpoint(client, db_session):
    repo = Repository(db_session)
    _seed(repo)

    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["readings_stored"] == 1
    assert data["events_stored"] == 1


def test_readings_endpoint(client, db_session):
    repo = Repository(db_session)
    _seed(repo)

    response = client.get("/readings?city=Ottawa&limit=10")
    assert response.status_code == 200
    data = response.json()
    assert "readings" in data
    assert len(data["readings"]) == 1
    reading = data["readings"][0]
    for field in (
        "id",
        "city",
        "observation_time",
        "observation_time_local",
        "temperature_2m",
        "apparent_temperature",
        "precipitation",
        "wind_speed_10m",
        "weather_code",
        "created_at",
    ):
        assert field in reading
    assert reading["city"] == "Ottawa"


def test_events_endpoint(client, db_session):
    repo = Repository(db_session)
    _seed(repo)

    response = client.get("/events?city=Ottawa&limit=10")
    assert response.status_code == 200
    data = response.json()
    assert "events" in data
    assert len(data["events"]) == 1
    event = data["events"][0]
    for field in (
        "id",
        "city",
        "occurred_at",
        "event_type",
        "title",
        "description",
        "reason",
        "metadata",
        "reading_id",
        "created_at",
    ):
        assert field in event


def test_readings_default_limit(client, db_session):
    repo = Repository(db_session)
    for i in range(3):
        repo.insert_reading(
            city="Toronto",
            observation_time=datetime(2026, 6, 1, i, 0, tzinfo=timezone.utc),
            temperature_2m=20.0 + i,
            apparent_temperature=19.0,
            precipitation=0.0,
            wind_speed_10m=10.0,
            weather_code=0,
        )
    repo.commit()

    response = client.get("/readings?city=Toronto")
    assert response.status_code == 200
    assert len(response.json()["readings"]) == 3
