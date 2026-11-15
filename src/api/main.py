"""FastAPI main application entry point."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError as PydanticValidationError

from src.api.routers import (
    accounts_router,
    auth_router,
    budgets_router,
    data_portability_router,
    goals_router,
    health_router,
    investments_router,
    loans_router,
    recurring_router,
    transactions_router,
)
from src.core.config import settings
from src.core.exceptions import (
    AppException,
    app_exception_handler,
    pydantic_validation_exception_handler,
    unhandled_exception_handler,
)
from src.core.logging import logger
from src.db.seed import seed_database
from src.db.session import SessionLocal


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan managing startup probes and teardown."""
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION} ({settings.ENVIRONMENT})")

    # Auto-seed default user/account in development
    try:
        with SessionLocal() as session:
            seed_database(session)
    except Exception as e:
        logger.error(f"Startup database check/seed error: {e}")

    yield

    logger.info("Shutting down application...")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="Production-oriented Personal Finance Tracker backend API.",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # CORS Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Exception Handlers
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(RequestValidationError, pydantic_validation_exception_handler)
    app.add_exception_handler(PydanticValidationError, pydantic_validation_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)

    # Root health endpoint
    app.include_router(health_router)

    # API v1 endpoints
    app.include_router(health_router, prefix=settings.API_V1_PREFIX)
    app.include_router(auth_router, prefix=settings.API_V1_PREFIX)
    app.include_router(accounts_router, prefix=settings.API_V1_PREFIX)
    app.include_router(transactions_router, prefix=settings.API_V1_PREFIX)
    app.include_router(budgets_router, prefix=settings.API_V1_PREFIX)
    app.include_router(goals_router, prefix=settings.API_V1_PREFIX)
    app.include_router(loans_router, prefix=settings.API_V1_PREFIX)
    app.include_router(investments_router, prefix=settings.API_V1_PREFIX)
    app.include_router(recurring_router, prefix=settings.API_V1_PREFIX)
    app.include_router(data_portability_router, prefix=settings.API_V1_PREFIX)

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.api.main:app",
        host=settings.BACKEND_HOST,
        port=settings.BACKEND_PORT,
        reload=settings.DEBUG,
    )
