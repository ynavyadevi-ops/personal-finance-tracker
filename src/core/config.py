"""Application configuration and environment settings management using Pydantic v2."""

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Core application settings validated against environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application metadata
    APP_NAME: str = "Personal Finance Tracker"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"

    # Networking & Hosts
    BACKEND_HOST: str = "127.0.0.1"
    BACKEND_PORT: int = 8000
    FRONTEND_PORT: int = 8501
    API_BASE_URL: str = "http://127.0.0.1:8000/api/v1"

    # Database URL (SQLite local, PostgreSQL production)
    DATABASE_URL: str = "sqlite:///./data/finance.db"

    # Security
    SECRET_KEY: str = Field(
        default="dev-insecure-secret-key-for-local-development-only-change-in-production",
        description="Application secret key used for session/token cryptographic operations.",
    )

    # CORS
    CORS_ORIGINS: str = "http://localhost:8501,http://127.0.0.1:8501"

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse comma-separated CORS origins into a list of strings."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @field_validator("ENVIRONMENT")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Validate environment string value."""
        allowed = {"development", "testing", "staging", "production"}
        if v.lower() not in allowed:
            raise ValueError(f"ENVIRONMENT must be one of {allowed}, got: {v}")
        return v.lower()


settings = Settings()
