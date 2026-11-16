"""API routers package."""

from src.api.routers.accounts import router as accounts_router
from src.api.routers.admin import router as admin_router
from src.api.routers.auth import router as auth_router
from src.api.routers.budgets import router as budgets_router
from src.api.routers.data_portability import router as data_portability_router
from src.api.routers.goals import router as goals_router
from src.api.routers.health import router as health_router
from src.api.routers.investments import router as investments_router
from src.api.routers.loans import router as loans_router
from src.api.routers.recurring import router as recurring_router
from src.api.routers.transactions import router as transactions_router

__all__ = [
    "accounts_router",
    "admin_router",
    "auth_router",
    "budgets_router",
    "data_portability_router",
    "goals_router",
    "health_router",
    "investments_router",
    "loans_router",
    "recurring_router",
    "transactions_router",
]
