"""Cryptographic security utilities: Argon2id password hashing and JWT token processing."""

from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher

from src.core.config import settings
from src.core.exceptions import AuthenticationError

# Initialize Argon2id password hasher through pwdlib
password_hash = PasswordHash((Argon2Hasher(),))


def hash_password(plain_password: str) -> str:
    """Hash a plaintext password using Argon2id with cryptographic salt."""
    if not plain_password:
        raise ValueError("Password cannot be empty.")
    return password_hash.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str | None) -> bool:
    """Verify a candidate password against an Argon2id hash.

    Returns False if hashed_password is None (e.g., unenrolled legacy accounts).
    """
    if not plain_password or not hashed_password:
        return False
    try:
        return password_hash.verify(plain_password, hashed_password)
    except Exception:
        return False


def create_access_token(
    user_id: str,
    expires_delta: timedelta | None = None,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    """Create a signed, short-lived JSON Web Token (JWT) for authenticated requests.

    Standard claims:
        - sub: Authenticated User ID (UUID string)
        - exp: Expiration timestamp (UTC)
        - iat: Issued-at timestamp (UTC)
        - type: Token classification ('access')
        - iss: Issuer identifier
    """
    now = datetime.now(UTC)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    payload: dict[str, Any] = {
        "sub": str(user_id),
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
        "type": "access",
        "iss": "personal-finance-tracker",
    }

    if extra_claims:
        # Prevent collision with protected standard claims
        sanitized = {k: v for k, v in extra_claims.items() if k not in payload}
        payload.update(sanitized)

    encoded = jwt.encode(
        payload=payload,
        key=settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    return str(encoded)


def decode_access_token(token: str) -> str:
    """Validate JWT token signature, expiration, and issuer.

    Returns:
        user_id (str): Extracted authenticated user identifier.

    Raises:
        AuthenticationError: If token is expired, has an invalid signature, or is malformed.
    """
    try:
        payload = jwt.decode(
            token,
            key=settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            issuer="personal-finance-tracker",
            options={"require": ["exp", "sub", "iat"]},
        )
        sub_val = payload.get("sub")
        if not isinstance(sub_val, str) or not sub_val:
            raise AuthenticationError("Token missing valid subject claim.")
        return sub_val
    except jwt.ExpiredSignatureError as e:
        raise AuthenticationError("Authentication token has expired.") from e
    except jwt.InvalidTokenError as e:
        raise AuthenticationError("Invalid authentication token signature or format.") from e
