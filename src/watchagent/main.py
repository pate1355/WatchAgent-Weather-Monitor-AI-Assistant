import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from watchagent.api.routes import router
from watchagent.config import Settings
from watchagent.logging_config import setup_logging
from watchagent.poller.loop import Poller
from watchagent.storage.database import init_db

logger = logging.getLogger(__name__)


def wait_for_db(settings: Settings, max_attempts: int = 30, delay: float = 2.0) -> None:
    import time

    from sqlalchemy import text
    from sqlalchemy.exc import OperationalError

    from watchagent.storage.database import get_engine

    init_db(settings)
    engine = get_engine()
    for attempt in range(1, max_attempts + 1):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("Database connection established", extra={"attempt": attempt})
            return
        except OperationalError:
            logger.warning("Database not ready, retrying", extra={"attempt": attempt})
            time.sleep(delay)
    raise RuntimeError("Could not connect to database")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings: Settings = app.state.settings
    setup_logging(settings)
    wait_for_db(settings)
    poller = None
    if settings.enable_poller:
        poller = Poller(settings)
        await poller.start()
        app.state.poller = poller
    yield
    if poller:
        await poller.stop()


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()
    app = FastAPI(title="WatchAgent", version="0.1.0", lifespan=lifespan)
    app.state.settings = settings
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
            "http://localhost:3000",
            "http://127.0.0.1:5173",
            "http://127.0.0.1:3000",
        ],
        allow_methods=["GET"],
        allow_headers=["*"],
    )
    app.include_router(router)
    return app


app = create_app()
