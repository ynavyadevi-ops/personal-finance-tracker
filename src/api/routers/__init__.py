"""API routers package."""

from src.api.routers.accounts import router as accounts_router
from src.api.routers.health import router as health_router

__all__ = ["health_router", "accounts_router"]
