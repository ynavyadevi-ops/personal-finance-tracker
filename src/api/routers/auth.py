"""FastAPI router implementing secure authentication endpoints."""

import json
import time
from collections import defaultdict

from fastapi import APIRouter, Depends, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.api.dependencies import get_current_user
from src.core.config import settings
from src.core.exceptions import AuthenticationError, PermissionDeniedError, ValidationError
from src.core.logging import logger
from src.core.security import create_access_token, hash_password, verify_password
from src.db.models.audit import AuditLog
from src.db.models.settings import SystemSettings
from src.db.models.user import User, UserRole
from src.db.session import get_db
from src.schemas.common import GenericResponse
from src.schemas.user import (
    PasswordChangeRequest,
    TokenResponse,
    UserRead,
    UserRegister,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])

# In-memory sliding-window rate limiter for registration / authentication attempts
# key -> list of timestamp floats
_ATTEMPT_TIMESTAMPS: dict[str, list[float]] = defaultdict(list)
RATE_LIMIT_WINDOW_SECONDS = 900  # 15 minutes
MAX_ATTEMPTS_PER_WINDOW = 20


def check_rate_limit(client_identifier: str) -> None:
    """Enforce request rate limiting on sensitive authentication operations."""
    now = time.time()
    cutoff = now - RATE_LIMIT_WINDOW_SECONDS
    # Clean up old timestamps
    timestamps = [t for t in _ATTEMPT_TIMESTAMPS[client_identifier] if t > cutoff]
    if len(timestamps) >= MAX_ATTEMPTS_PER_WINDOW:
        logger.warning(f"Rate limit exceeded for client: {client_identifier}")
        raise ValidationError(
            "Too many authentication attempts. Please wait 15 minutes before retrying."
        )
    timestamps.append(now)
    _ATTEMPT_TIMESTAMPS[client_identifier] = timestamps


@router.post(
    "/register",
    response_model=GenericResponse[UserRead],
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account with Argon2id password hashing",
)
def register_user(
    payload: UserRegister,
    request: Request,
    db: Session = Depends(get_db),
) -> GenericResponse[UserRead]:
    """Register a new user account strictly enforcing USER role and unique email."""
    client_ip = request.client.host if request.client else "unknown"
    check_rate_limit(f"reg:{client_ip}")

    # 1. Verify platform registration policy
    setting = db.execute(
        select(SystemSettings).where(SystemSettings.key == "registration_enabled")
    ).scalar_one_or_none()
    if setting and setting.value.lower() == "false":
        logger.warning(f"Registration rejected: public registration is disabled. IP: {client_ip}")
        raise PermissionDeniedError(
            "Public user registration is currently disabled by administrator."
        )

    clean_email = payload.email.strip().lower()

    # 2. Check for existing user with safe generic response (prevents account enumeration)
    existing_user = db.execute(select(User).where(User.email == clean_email)).scalar_one_or_none()
    if existing_user:
        logger.info(
            f"Registration rejected: account already exists for normalized email: {clean_email}"
        )
        raise ValidationError("Unable to complete registration with the provided details.")

    # 3. Create user with strictly assigned USER role
    user = User(
        name=payload.name.strip(),
        email=clean_email,
        hashed_password=hash_password(payload.password),
        role=UserRole.USER,
        is_active=True,
        must_change_password=False,
    )
    db.add(user)
    db.flush()

    # 4. Log registration event in immutable audit log
    audit_entry = AuditLog(
        user_id=user.id,
        action="USER_REGISTRATION",
        entity_name="USER",
        entity_id=user.id,
        new_values=json.dumps({"email": user.email, "role": user.role.value}),
        ip_address=client_ip,
        user_agent=request.headers.get("user-agent"),
    )
    db.add(audit_entry)
    db.commit()
    db.refresh(user)

    logger.info(f"New user registered successfully: {user.id} ({clean_email})")
    return GenericResponse(
        success=True,
        data=UserRead.model_validate(user),
    )


@router.post(
    "/token",
    response_model=TokenResponse,
    summary="OAuth2 Password Bearer login issuing JWT access token",
)
def login_for_access_token(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> TokenResponse:
    """Authenticate credentials against Argon2id hash and issue a signed JWT token."""
    email = form_data.username.strip().lower()

    user = db.execute(select(User).where(User.email == email)).scalar_one_or_none()

    if not user or not user.hashed_password:
        logger.warning(f"Failed login attempt for nonexistent or passwordless user: {email}")
        raise AuthenticationError("Invalid email or password.")

    if not user.is_active:
        logger.warning(f"Login rejected: account {user.id} ({email}) is disabled.")
        raise AuthenticationError(
            "This user account has been disabled. Please contact an administrator."
        )

    if not verify_password(form_data.password, user.hashed_password):
        logger.warning(f"Invalid password login attempt for user: {email}")
        raise AuthenticationError("Invalid email or password.")

    token = create_access_token(
        user_id=user.id,
        extra_claims={"role": user.role.value},
    )
    return TokenResponse(
        access_token=token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        must_change_password=user.must_change_password,
        role=user.role.value,
    )


@router.get(
    "/me",
    response_model=GenericResponse[UserRead],
    summary="Retrieve authenticated user profile",
)
def get_authenticated_user_profile(
    current_user: User = Depends(get_current_user),
) -> GenericResponse[UserRead]:
    """Return the profile of the verified authenticated user (never exposes password hashes)."""
    return GenericResponse(
        success=True,
        data=UserRead.model_validate(current_user),
    )


@router.post(
    "/change-password",
    response_model=GenericResponse[dict[str, str]],
    summary="Change password for the authenticated user",
)
def change_password(
    payload: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> GenericResponse[dict[str, str]]:
    """Update password for the current authenticated user."""
    if not current_user.hashed_password or not verify_password(
        payload.old_password, current_user.hashed_password
    ):
        raise ValidationError("Current password is incorrect.")

    current_user.hashed_password = hash_password(payload.new_password)
    current_user.must_change_password = False

    audit = AuditLog(
        user_id=current_user.id,
        action="PASSWORD_CHANGE",
        entity_name="USER",
        entity_id=current_user.id,
        new_values=json.dumps({"must_change_password": False}),
    )
    db.add(audit)
    db.commit()

    logger.info(f"Password changed successfully for user: {current_user.id}")
    return GenericResponse(
        success=True,
        data={"message": "Password changed successfully."},
    )
