from fastapi import APIRouter, HTTPException, status

from app.core.config import settings
from app.database import check_database_health

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check():
    database_ready, database_error = check_database_health()
    if not database_ready:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"status": "degraded", "database": "unavailable", "error": database_error},
        )
    return {
        "status": "ok",
        "app_name": settings.APP_NAME,
        "environment": settings.ENVIRONMENT,
        "ai_mock_mode": settings.AI_MOCK_MODE,
        "database": "ok",
    }
