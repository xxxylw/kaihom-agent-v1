from fastapi import APIRouter, Depends

from app.core.config import Settings, get_settings


router = APIRouter(tags=["system"])


@router.get("/health")
def health_check(settings: Settings = Depends(get_settings)) -> dict[str, str]:
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
    }
