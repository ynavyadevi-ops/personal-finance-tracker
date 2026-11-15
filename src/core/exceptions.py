"""Centralized domain exceptions and FastAPI HTTP exception handlers."""

from typing import Any

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError as PydanticValidationError


class AppException(Exception):
    """Base application domain exception."""

    def __init__(
        self,
        message: str,
        code: str = "APP_ERROR",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}


class NotFoundError(AppException):
    """Raised when an entity or resource is not found."""

    def __init__(
        self,
        message: str = "Resource not found",
        code: str = "NOT_FOUND",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            code=code,
            status_code=status.HTTP_404_NOT_FOUND,
            details=details,
        )


class ValidationError(AppException):
    """Raised when a business validation rule is violated."""

    def __init__(
        self,
        message: str = "Validation failed",
        code: str = "VALIDATION_ERROR",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            code=code,
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            details=details,
        )


class ConflictError(AppException):
    """Raised when an action conflicts with existing state."""

    def __init__(
        self,
        message: str = "Resource conflict occurred",
        code: str = "CONFLICT",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            code=code,
            status_code=status.HTTP_409_CONFLICT,
            details=details,
        )


class PermissionDeniedError(AppException):
    """Raised when a user attempts to access an unauthorized or cross-tenant resource."""

    def __init__(
        self,
        message: str = "Permission denied",
        code: str = "FORBIDDEN",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            code=code,
            status_code=status.HTTP_403_FORBIDDEN,
            details=details,
        )


class CurrencyMismatchError(ValidationError):
    """Raised when a financial operation involves incompatible currencies."""

    def __init__(
        self,
        message: str = "Currency mismatch between accounts",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            code="CURRENCY_MISMATCH",
            details=details,
        )


class InsufficientUnitsError(ValidationError):
    """Raised when attempting to sell more investment units than currently held."""

    def __init__(
        self,
        message: str = "Insufficient units available for sale",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            code="INSUFFICIENT_UNITS",
            details=details,
        )


async def app_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Serialize custom AppException into standardized JSON response."""
    app_exc = exc if isinstance(exc, AppException) else AppException(str(exc))
    return JSONResponse(
        status_code=app_exc.status_code,
        content={
            "success": False,
            "data": None,
            "error": {
                "code": app_exc.code,
                "message": app_exc.message,
                "details": app_exc.details,
            },
        },
    )


async def pydantic_validation_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Serialize validation errors into clean standardized API error envelopes."""
    errors = []
    if isinstance(exc, RequestValidationError | PydanticValidationError):
        for err in exc.errors():
            field_path = ".".join(str(loc) for loc in err.get("loc", []))
            errors.append(
                {
                    "field": field_path,
                    "message": err.get("msg", "Invalid value"),
                    "type": err.get("type", "value_error"),
                }
            )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content={
            "success": False,
            "data": None,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request payload failed validation schema.",
                "details": {"validation_errors": errors},
            },
        },
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle uncaught internal exceptions safely without leaking stack traces."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "data": None,
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected internal server error occurred.",
                "details": {},
            },
        },
    )
