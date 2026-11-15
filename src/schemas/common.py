"""Common shared Pydantic response models and schemas."""

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class GenericResponse(BaseModel, Generic[T]):
    """Standardized top-level API JSON response envelope."""

    success: bool = Field(default=True, description="Indicates if the operation succeeded.")
    data: T | None = Field(default=None, description="Response payload.")
    error: dict[str, Any] | None = Field(default=None, description="Error details if unsuccessful.")
    meta: dict[str, Any] | None = Field(
        default=None, description="Metadata such as pagination or counts."
    )


class HealthResponse(BaseModel):
    """Health check response schema. Never exposes credentials or secrets."""

    status: str = Field(description="System operational status string.")
    app_name: str = Field(description="Application title.")
    version: str = Field(description="Semantic version.")
    environment: str = Field(description="Current runtime environment.")
    database_connected: bool = Field(description="Status of database connectivity.")
