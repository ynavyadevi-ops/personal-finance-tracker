"""Administrative CLI tool for secure bootstrapping of administrator accounts."""

from __future__ import annotations

import argparse
import getpass
import json
import secrets
import string
import sys
from collections.abc import Callable, Sequence
from typing import TextIO

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.core.security import hash_password
from src.db.models.audit import AuditLog
from src.db.models.user import User, UserRole
from src.db.session import SessionLocal
from src.schemas.user import validate_password_complexity


def generate_secure_password(length: int = 32) -> str:
    """Generate a high-entropy password satisfying complexity constraints."""
    chars = string.ascii_letters + string.digits + "!@#$%^&*()_+-="
    while True:
        pwd = "".join(secrets.choice(chars) for _ in range(length))
        try:
            validate_password_complexity(pwd)
            return pwd
        except ValueError:
            continue


def bootstrap_admin(
    email: str = "admin@local.dev",
    name: str = "Administrator",
    generate: bool = False,
    session: Session | None = None,
    password_prompt: Callable[[], str] = lambda: getpass.getpass("Enter administrator password: "),
    confirm_prompt: Callable[[], str] = lambda: getpass.getpass("Confirm administrator password: "),
    elevation_confirm_prompt: Callable[[str], bool] | None = None,
    stdout: TextIO = sys.stdout,
    stderr: TextIO = sys.stderr,
) -> int:
    """Bootstrap an administrator account idempotently.

    Enforces:
    - Safe defaults and email normalization.
    - Idempotency: aborts cleanly if an active admin already exists.
    - Operator confirmation before elevating existing USER accounts.
    - Argon2id password hashing.
    - Sets must_change_password=True for initial login.
    - Audit logging of the bootstrap event.
    - Masked or securely generated credentials.
    """
    clean_email = email.strip().lower()
    if not clean_email:
        stderr.write("Error: An email address must be provided.\n")
        return 1

    own_session = False
    if session is None:
        session = SessionLocal()
        own_session = True

    try:
        # 1. Idempotency check: see if an active admin already exists
        existing_admin = (
            session.execute(
                select(User).where(User.role == UserRole.ADMIN, User.is_active.is_(True))
            )
            .scalars()
            .first()
        )

        if existing_admin:
            stdout.write(
                f"[INFO] An active administrator account ('{existing_admin.email}') already exists.\n"
                "Bootstrap is idempotent; no changes made.\n"
            )
            return 0

        # 2. Check if target user already exists
        target_user = session.execute(
            select(User).where(User.email == clean_email)
        ).scalar_one_or_none()

        if target_user and target_user.role == UserRole.USER:
            if elevation_confirm_prompt is None:

                def default_elevation_confirm(target_addr: str) -> bool:
                    try:
                        resp = input(
                            f"Account '{target_addr}' currently exists with role 'USER'.\n"
                            "Are you sure you want to elevate this account to ADMINISTRATOR? [y/N]: "
                        )
                        return resp.strip().lower() in ("y", "yes")
                    except (KeyboardInterrupt, EOFError):
                        return False

                elevation_confirm_prompt = default_elevation_confirm

            if not elevation_confirm_prompt(clean_email):
                stdout.write("Elevation cancelled by operator.\n")
                return 1

        # 3. Handle password acquisition
        if generate:
            password = generate_secure_password()
            stdout.write("\n" + "=" * 70 + "\n")
            stdout.write(
                "[SECURITY WARNING] A temporary administrative password has been generated.\n"
            )
            stdout.write("Store it securely immediately; it will NOT be displayed again.\n")
            stdout.write(f"Temporary Password: {password}\n")
            stdout.write("=" * 70 + "\n\n")
        else:
            try:
                password = password_prompt()
                confirm = confirm_prompt()
            except (KeyboardInterrupt, EOFError):
                stderr.write("\nBootstrap aborted by operator.\n")
                return 1

            if password != confirm:
                stderr.write("Error: Passwords do not match.\n")
                return 1

            try:
                validate_password_complexity(password)
            except ValueError as err:
                stderr.write(f"Error: {err}\n")
                return 1

        # 4. Create or elevate user
        hashed = hash_password(password)
        if target_user:
            target_user.role = UserRole.ADMIN
            target_user.is_active = True
            target_user.must_change_password = True
            target_user.hashed_password = hashed
            user_to_log = target_user
        else:
            new_user = User(
                email=clean_email,
                name=name.strip() or "Administrator",
                role=UserRole.ADMIN,
                is_active=True,
                must_change_password=True,
                hashed_password=hashed,
            )
            session.add(new_user)
            user_to_log = new_user

        session.flush()

        audit = AuditLog(
            user_id=user_to_log.id,
            action="ADMIN_BOOTSTRAP",
            entity_name="USER",
            entity_id=user_to_log.id,
            new_values=json.dumps({"role": "ADMIN", "must_change_password": True}),
        )
        session.add(audit)
        session.commit()

        stdout.write(
            f"[SUCCESS] Administrator account '{user_to_log.email}' bootstrapped successfully.\n"
            "[NOTICE] First login will require a password change.\n"
        )
        return 0

    except Exception as exc:
        session.rollback()
        stderr.write(f"Error during administrative bootstrap: {exc}\n")
        return 1
    finally:
        if own_session:
            session.close()


def main(
    argv: Sequence[str] | None = None,
    session: Session | None = None,
    stdout: TextIO = sys.stdout,
    stderr: TextIO = sys.stderr,
) -> int:
    """Entrypoint for administrative bootstrap CLI."""
    parser = argparse.ArgumentParser(
        prog="python -m src.cli.bootstrap_admin",
        description="Bootstrap initial administrator account with secure role assignment and auditing.",
    )
    parser.add_argument(
        "--email",
        default="admin@local.dev",
        help="Email address for administrator account (default: admin@local.dev)",
    )
    parser.add_argument(
        "--name",
        default="admin",
        help="Full name or username for administrator account (default: admin)",
    )
    parser.add_argument(
        "--generate",
        action="store_true",
        help="Generate a cryptographically secure random password instead of prompting.",
    )

    try:
        parsed = parser.parse_args(argv)
    except SystemExit as e:
        return e.code if isinstance(e.code, int) else 1

    return bootstrap_admin(
        email=parsed.email,
        name=parsed.name,
        generate=parsed.generate,
        session=session,
        stdout=stdout,
        stderr=stderr,
    )


if __name__ == "__main__":
    sys.exit(main())
