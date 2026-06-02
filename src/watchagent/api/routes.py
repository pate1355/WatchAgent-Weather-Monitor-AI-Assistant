from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from watchagent.api.schemas import (
    EventOut,
    EventsResponse,
    HealthResponse,
    ReadingOut,
    ReadingsResponse,
)
from watchagent.cities import CITY_NAMES
from watchagent.storage.database import get_db
from watchagent.storage.repo import Repository

router = APIRouter()


def _validate_city(city: str | None) -> None:
    if city is not None and city not in CITY_NAMES:
        raise HTTPException(status_code=400, detail=f"Unknown city: {city}")


@router.get("/health", response_model=HealthResponse)
def health(db: Session = Depends(get_db)) -> HealthResponse:
    repo = Repository(db)
    return HealthResponse(
        status="ok",
        readings_stored=repo.count_readings(),
        events_stored=repo.count_events(),
    )


@router.get("/readings", response_model=ReadingsResponse)
def readings(
    city: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    db: Session = Depends(get_db),
) -> ReadingsResponse:
    _validate_city(city)
    repo = Repository(db)
    items = repo.list_readings(city=city, limit=limit)
    return ReadingsResponse(readings=[ReadingOut.model_validate(r) for r in items])


@router.get("/events", response_model=EventsResponse)
def events(
    city: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    db: Session = Depends(get_db),
) -> EventsResponse:
    _validate_city(city)
    repo = Repository(db)
    items = repo.list_events(city=city, limit=limit)
    return EventsResponse(events=[EventOut.model_validate(e) for e in items])
