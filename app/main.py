from fastapi import FastAPI

from app.api.health import router as health_router
from app.api.mock_kaihong import router as mock_kaihong_router
from app.api.uploads import router as uploads_router
from app.core.config import get_settings
from app.db.session import create_db_and_tables


def create_app() -> FastAPI:
    settings = get_settings()
    create_db_and_tables()
    app = FastAPI(
        title=settings.app_name,
        description="Mock-first logistics order entry Agent backend",
        version=settings.app_version,
    )
    app.include_router(health_router)
    app.include_router(mock_kaihong_router)
    app.include_router(uploads_router)
    return app


app = create_app()
