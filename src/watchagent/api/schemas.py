from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_serializer, model_validator

from watchagent.time_utils import local_iso_from_utc


def _utc_z(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class HealthResponse(BaseModel):
    status: str
    readings_stored: int
    events_stored: int


class ReadingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    city: str
    observation_time: datetime
    observation_time_local: str | None = None
    temperature_2m: float
    apparent_temperature: float
    precipitation: float
    wind_speed_10m: float
    weather_code: int
    created_at: datetime

    @model_validator(mode="after")
    def fill_local_time(self) -> "ReadingOut":
        if not self.observation_time_local:
            self.observation_time_local = local_iso_from_utc(
                self.observation_time, self.city
            )
        return self

    @field_serializer("observation_time", "created_at")
    def serialize_utc(self, dt: datetime) -> str:
        return _utc_z(dt)


class ReadingsResponse(BaseModel):
    readings: list[ReadingOut]


class EventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int
    city: str | None
    occurred_at: datetime
    occurred_at_local: str | None = None
    event_type: str
    title: str
    description: str
    reason: str
    metadata: dict[str, Any] = Field(validation_alias="event_metadata")
    reading_id: int | None
    created_at: datetime

    @model_validator(mode="after")
    def fill_local_time(self) -> "EventOut":
        if not self.occurred_at_local and self.city:
            self.occurred_at_local = local_iso_from_utc(self.occurred_at, self.city)
        return self

    @field_serializer("occurred_at", "created_at")
    def serialize_utc(self, dt: datetime) -> str:
        return _utc_z(dt)


class EventsResponse(BaseModel):
    events: list[EventOut]
