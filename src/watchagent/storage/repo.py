from datetime import datetime, timedelta, timezone

from sqlalchemy import desc, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from watchagent.storage.models import Event, Reading


class Repository:
    def __init__(self, session: Session):
        self.session = session

    def insert_reading(
        self,
        *,
        city: str,
        observation_time: datetime,
        observation_time_local: str | None = None,
        temperature_2m: float,
        apparent_temperature: float,
        precipitation: float,
        wind_speed_10m: float,
        weather_code: int,
    ) -> Reading | None:
        reading = Reading(
            city=city,
            observation_time=observation_time,
            observation_time_local=observation_time_local,
            temperature_2m=temperature_2m,
            apparent_temperature=apparent_temperature,
            precipitation=precipitation,
            wind_speed_10m=wind_speed_10m,
            weather_code=weather_code,
        )
        try:
            with self.session.begin_nested():
                self.session.add(reading)
                self.session.flush()
            return reading
        except IntegrityError:
            return None

    def get_previous_reading(self, city: str, before: datetime) -> Reading | None:
        stmt = (
            select(Reading)
            .where(Reading.city == city, Reading.observation_time < before)
            .order_by(desc(Reading.observation_time))
            .limit(1)
        )
        return self.session.scalar(stmt)

    def get_latest_reading(self, city: str) -> Reading | None:
        stmt = (
            select(Reading)
            .where(Reading.city == city)
            .order_by(desc(Reading.observation_time))
            .limit(1)
        )
        return self.session.scalar(stmt)

    def get_latest_readings_all_cities(self) -> dict[str, Reading]:
        result: dict[str, Reading] = {}
        cities_stmt = select(Reading.city).distinct()
        for (city,) in self.session.execute(cities_stmt):
            latest = self.get_latest_reading(city)
            if latest:
                result[city] = latest
        return result

    def insert_event(
        self,
        *,
        city: str | None,
        occurred_at: datetime,
        event_type: str,
        title: str,
        description: str,
        reason: str,
        metadata: dict,
        reading_id: int | None = None,
    ) -> Event:
        event = Event(
            city=city,
            occurred_at=occurred_at,
            event_type=event_type,
            title=title,
            description=description,
            reason=reason,
            event_metadata=metadata,
            reading_id=reading_id,
        )
        self.session.add(event)
        self.session.flush()
        return event

    def has_recent_event(
        self, city: str | None, event_type: str, since: datetime
    ) -> bool:
        stmt = select(func.count()).select_from(Event).where(
            Event.event_type == event_type,
            Event.occurred_at >= since,
        )
        if city is None:
            stmt = stmt.where(Event.city.is_(None))
        else:
            stmt = stmt.where(Event.city == city)
        return (self.session.scalar(stmt) or 0) > 0

    def count_readings(self) -> int:
        return self.session.scalar(select(func.count()).select_from(Reading)) or 0

    def count_events(self) -> int:
        return self.session.scalar(select(func.count()).select_from(Event)) or 0

    def list_readings(self, city: str | None = None, limit: int = 50) -> list[Reading]:
        stmt = select(Reading).order_by(desc(Reading.observation_time)).limit(limit)
        if city:
            stmt = stmt.where(Reading.city == city)
        return list(self.session.scalars(stmt))

    def list_events(self, city: str | None = None, limit: int = 50) -> list[Event]:
        stmt = select(Event).order_by(desc(Event.occurred_at)).limit(limit)
        if city:
            stmt = stmt.where(Event.city == city)
        return list(self.session.scalars(stmt))

    def commit(self) -> None:
        self.session.commit()

    def rollback(self) -> None:
        self.session.rollback()

    @staticmethod
    def cooldown_since(minutes: int) -> datetime:
        return datetime.now(timezone.utc) - timedelta(minutes=minutes)
