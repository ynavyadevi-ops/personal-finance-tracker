"""Unit tests for the administrative bootstrap CLI (src/cli/bootstrap_admin.py)."""

from __future__ import annotations

import io
import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.cli.bootstrap_admin import bootstrap_admin, generate_secure_password
from src.core.security import hash_password, verify_password
from src.db.models.audit import AuditLog
from src.db.models.user import User, UserRole
from src.schemas.user import validate_password_complexity


def test_generate_secure_password() -> None:
    """Verify generated password meets complexity criteria and length constraints."""
    pwd = generate_secure_password(32)
    assert len(pwd) == 32
    # Ensure validate_password_complexity does not raise
    assert validate_password_complexity(pwd) == pwd


def test_bootstrap_admin_success_interactive(db_session: Session) -> None:
    """Verify clean bootstrap of administrator account with interactive prompts."""
    stdout = io.StringIO()
    stderr = io.StringIO()

    exit_code = bootstrap_admin(
        email="superadmin@local.dev",
        generate=False,
        session=db_session,
        password_prompt=lambda: "AdminPass123!@#",
        confirm_prompt=lambda: "AdminPass123!@#",
        stdout=stdout,
        stderr=stderr,
    )

    assert exit_code == 0
    assert (
        "Administrator account 'superadmin@local.dev' bootstrapped successfully"
        in stdout.getvalue()
    )
    assert stderr.getvalue() == ""

    # Verify user attributes
    admin = db_session.execute(
        select(User).where(User.email == "superadmin@local.dev")
    ).scalar_one()

    assert admin.role == UserRole.ADMIN
    assert admin.is_active is True
    assert admin.must_change_password is True
    assert admin.hashed_password is not None
    assert verify_password("AdminPass123!@#", admin.hashed_password) is True

    # Confidentiality assertion: plaintext password never in stdout/stderr
    assert "AdminPass123!@#" not in stdout.getvalue()

    # Audit log check
    audit = db_session.execute(
        select(AuditLog).where(AuditLog.user_id == admin.id, AuditLog.action == "ADMIN_BOOTSTRAP")
    ).scalar_one_or_none()
    assert audit is not None


def test_bootstrap_admin_with_generate(db_session: Session) -> None:
    """Verify administrator bootstrap using --generate flag."""
    stdout = io.StringIO()
    stderr = io.StringIO()

    exit_code = bootstrap_admin(
        email="generated_admin@local.dev",
        generate=True,
        session=db_session,
        stdout=stdout,
        stderr=stderr,
    )

    assert exit_code == 0
    out = stdout.getvalue()
    assert "SECURITY WARNING" in out
    assert "Temporary Password:" in out

    # Extract temporary password
    match = re.search(r"Temporary Password:\s*(\S+)", out)
    assert match is not None
    generated_pwd = match.group(1)

    admin = db_session.execute(
        select(User).where(User.email == "generated_admin@local.dev")
    ).scalar_one()
    assert verify_password(generated_pwd, admin.hashed_password) is True
    assert admin.role == UserRole.ADMIN
    assert admin.must_change_password is True


def test_bootstrap_admin_idempotent_when_active_admin_exists(db_session: Session) -> None:
    """Verify CLI is idempotent and makes no changes if an active administrator exists."""
    # Seed an active admin
    existing = User(
        id="existing-admin-id",
        name="Existing Admin",
        email="existing_admin@local.dev",
        role=UserRole.ADMIN,
        is_active=True,
        hashed_password=hash_password("Pass1234!@#$"),
    )
    db_session.add(existing)
    db_session.flush()

    stdout = io.StringIO()
    stderr = io.StringIO()

    exit_code = bootstrap_admin(
        email="new_admin@local.dev",
        generate=True,
        session=db_session,
        stdout=stdout,
        stderr=stderr,
    )

    assert exit_code == 0
    assert (
        "An active administrator account ('existing_admin@local.dev') already exists"
        in stdout.getvalue()
    )
    assert "Bootstrap is idempotent; no changes made" in stdout.getvalue()

    # Verify new user was NOT created
    new_user = db_session.execute(
        select(User).where(User.email == "new_admin@local.dev")
    ).scalar_one_or_none()
    assert new_user is None


def test_bootstrap_admin_elevate_user_confirmed(db_session: Session) -> None:
    """Verify elevating an existing standard USER account with explicit operator confirmation."""
    existing_user = User(
        id="standard-user-id",
        name="Standard User",
        email="elevate_me@local.dev",
        role=UserRole.USER,
        is_active=True,
        hashed_password=hash_password("UserPass123!@#"),
    )
    db_session.add(existing_user)
    db_session.flush()

    stdout = io.StringIO()
    stderr = io.StringIO()

    exit_code = bootstrap_admin(
        email="elevate_me@local.dev",
        generate=False,
        session=db_session,
        password_prompt=lambda: "ElevatedAdminPass999!",
        confirm_prompt=lambda: "ElevatedAdminPass999!",
        elevation_confirm_prompt=lambda _target: True,
        stdout=stdout,
        stderr=stderr,
    )

    assert exit_code == 0
    db_session.refresh(existing_user)
    assert existing_user.role == UserRole.ADMIN
    assert existing_user.must_change_password is True
    assert verify_password("ElevatedAdminPass999!", existing_user.hashed_password) is True


def test_bootstrap_admin_elevate_user_cancelled(db_session: Session) -> None:
    """Verify operator cancelling elevation preserves standard USER role."""
    existing_user = User(
        id="standard-user-id-2",
        name="Standard User 2",
        email="stay_user@local.dev",
        role=UserRole.USER,
        is_active=True,
        hashed_password=hash_password("OriginalPassword123!"),
    )
    db_session.add(existing_user)
    db_session.flush()

    stdout = io.StringIO()
    stderr = io.StringIO()

    exit_code = bootstrap_admin(
        email="stay_user@local.dev",
        generate=False,
        session=db_session,
        password_prompt=lambda: "ElevatedAdminPass999!",
        confirm_prompt=lambda: "ElevatedAdminPass999!",
        elevation_confirm_prompt=lambda _target: False,
        stdout=stdout,
        stderr=stderr,
    )

    assert exit_code == 1
    assert "Elevation cancelled by operator" in stdout.getvalue()

    db_session.refresh(existing_user)
    assert existing_user.role == UserRole.USER
    assert verify_password("OriginalPassword123!", existing_user.hashed_password) is True


def test_bootstrap_admin_password_mismatch(db_session: Session) -> None:
    """Verify password mismatch aborts without persisting user."""
    stdout = io.StringIO()
    stderr = io.StringIO()

    exit_code = bootstrap_admin(
        email="mismatch@local.dev",
        generate=False,
        session=db_session,
        password_prompt=lambda: "ValidPass123!@#",
        confirm_prompt=lambda: "DifferentPass123!@#",
        stdout=stdout,
        stderr=stderr,
    )

    assert exit_code == 1
    assert "Passwords do not match" in stderr.getvalue()

    user = db_session.execute(
        select(User).where(User.email == "mismatch@local.dev")
    ).scalar_one_or_none()
    assert user is None


def test_bootstrap_admin_weak_password(db_session: Session) -> None:
    """Verify weak password failing complexity validation aborts without persisting user."""
    stdout = io.StringIO()
    stderr = io.StringIO()

    exit_code = bootstrap_admin(
        email="weak@local.dev",
        generate=False,
        session=db_session,
        password_prompt=lambda: "weakpass",
        confirm_prompt=lambda: "weakpass",
        stdout=stdout,
        stderr=stderr,
    )

    assert exit_code == 1
    assert "Password must contain at least one uppercase letter" in stderr.getvalue()
