import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from watchagent.config import Settings
from watchagent.main import create_app
from watchagent.storage.database import get_db, init_db
from watchagent.storage.models import Base


@pytest.fixture
def settings() -> Settings:
    return Settings(
        database_url="sqlite:///:memory:",
        enable_poller=False,
        event_cooldown_minutes=60,
    )


@pytest.fixture
def engine(settings):
    eng = create_engine(
        settings.database_url,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(eng)
    yield eng
    Base.metadata.drop_all(eng)


@pytest.fixture
def session_factory(engine):
    return sessionmaker(bind=engine, autocommit=False, autoflush=False)


@pytest.fixture
def db_session(session_factory):
    session = session_factory()
    yield session
    session.close()


@pytest.fixture
def client(settings, engine, session_factory):
    import watchagent.storage.database as db_module

    db_module._engine = engine
    db_module._SessionLocal = session_factory

    def override_get_db():
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    app = create_app(settings)
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
