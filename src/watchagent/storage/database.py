from collections.abc import Generator

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session, sessionmaker

from watchagent.config import Settings
from watchagent.storage.models import Base

_engine = None
_SessionLocal = None


def init_db(settings: Settings) -> None:
    global _engine, _SessionLocal
    if _engine is not None:
        return
    _engine = create_engine(settings.database_url, pool_pre_ping=True)
    _SessionLocal = sessionmaker(bind=_engine, autocommit=False, autoflush=False)
    Base.metadata.create_all(bind=_engine)
    _migrate_readings_local_time(_engine)


def _migrate_readings_local_time(engine) -> None:
    """Add observation_time_local for databases created before this column existed."""
    if not inspect(engine).has_table("readings"):
        return
    columns = {c["name"] for c in inspect(engine).get_columns("readings")}
    if "observation_time_local" in columns:
        return
    with engine.connect() as conn:
        conn.execute(
            text("ALTER TABLE readings ADD COLUMN observation_time_local VARCHAR(32)")
        )
        conn.commit()


def get_engine():
    if _engine is None:
        raise RuntimeError("Database not initialized")
    return _engine


def get_session_factory():
    if _SessionLocal is None:
        raise RuntimeError("Database not initialized")
    return _SessionLocal


def get_db() -> Generator[Session, None, None]:
    session = get_session_factory()()
    try:
        yield session
    finally:
        session.close()
