"""Health check router reporting backend status and database connectivity."""

from fastapi import APIRouter, Depends, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from src.core.config import settings
from src.core.logging import logger
from src.db.session import get_db
from src.schemas.common import GenericResponse, HealthResponse

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=GenericResponse[HealthResponse],
    status_code=status.HTTP_200_OK,
    summary="Application Health Check",
    description="Reports system operational status. Does not disclose secrets or credentials.",
)
def health_check(db: Session = Depends(get_db)) -> GenericResponse[HealthResponse]:
    """Execute connectivity probe and return system health summary."""
    db_connected = False
    try:
        db.execute(text("SELECT 1"))
        db_connected = True
    except Exception as e:
        logger.error(f"Health check database connectivity probe failed: {e}")

    system_status = "healthy" if db_connected else "degraded"

    payload = HealthResponse(
        status=system_status,
        app_name=settings.APP_NAME,
        version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT,
        database_connected=db_connected,
    )

    return GenericResponse(
        success=db_connected,
        data=payload,
    )
