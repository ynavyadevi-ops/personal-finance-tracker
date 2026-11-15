"""FastAPI router implementing secure authentication endpoints."""

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.api.dependencies import get_current_user
from src.core.config import settings
from src.core.exceptions import AuthenticationError, ConflictError, NotFoundError
from src.core.security import create_access_token, hash_password, verify_password
from src.db.models.user import User
from src.db.session import get_db
from src.schemas.common import GenericResponse
from src.schemas.user import (
    TokenResponse,
    UserEnrollPassword,
    UserRead,
    UserRegister,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=GenericResponse[UserRead],
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account with Argon2id password hashing",
)
def register_user(
    payload: UserRegister,
    db: Session = Depends(get_db),
) -> GenericResponse[UserRead]:
    """Register a new user with email and secure password."""
    stmt = select(User).where(User.email == payload.email)
    existing_user = db.execute(stmt).scalar_one_or_none()
    if existing_user:
        raise ConflictError(f"A user with email '{payload.email}' already exists.")

    user = User(
        name=payload.name,
        email=payload.email,
        hashed_password=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

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
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> TokenResponse:
    """Authenticate credentials against Argon2id hash and issue a signed JWT token."""
    email = form_data.username.strip().lower()
    stmt = select(User).where(User.email == email)
    user = db.execute(stmt).scalar_one_or_none()

    if not user or not user.hashed_password:
        raise AuthenticationError("Invalid email or password.")

    if not verify_password(form_data.password, user.hashed_password):
        raise AuthenticationError("Invalid email or password.")

    token = create_access_token(user_id=user.id)
    return TokenResponse(
        access_token=token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post(
    "/enroll",
    response_model=GenericResponse[UserRead],
    summary="Safe initial password enrollment for existing legacy user accounts",
)
def enroll_legacy_password(
    payload: UserEnrollPassword,
    db: Session = Depends(get_db),
) -> GenericResponse[UserRead]:
    """Provide safe initial password enrollment for pre-existing accounts that lack a password."""
    email = payload.email.strip().lower()
    stmt = select(User).where(User.email == email)
    user = db.execute(stmt).scalar_one_or_none()

    if not user:
        raise NotFoundError(f"User account with email '{payload.email}' was not found.")

    if user.hashed_password is not None:
        raise ConflictError(
            "This user account is already enrolled with a password. Please use standard login."
        )

    user.hashed_password = hash_password(payload.new_password)
    db.commit()
    db.refresh(user)

    return GenericResponse(
        success=True,
        data=UserRead.model_validate(user),
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
