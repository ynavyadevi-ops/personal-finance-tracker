"""Administrative CLI tool for secure manual password enrollment of legacy accounts."""

from __future__ import annotations

import argparse
import getpass
import sys
from collections.abc import Callable, Sequence
from typing import TextIO

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.core.security import hash_password
from src.db.models.user import User
from src.db.session import SessionLocal


def enroll_user(
    email: str,
    session: Session,
    password_prompt: Callable[[], str] = lambda: getpass.getpass("Enter new password: "),
    confirm_prompt: Callable[[], str] = lambda: getpass.getpass("Confirm new password: "),
    confirmation_prompt: Callable[[str], bool] | None = None,
    stdout: TextIO = sys.stdout,
    stderr: TextIO = sys.stderr,
) -> int:
    """Enroll password for an existing unauthenticated user account.

    Enforces:
    - User existence check before prompting credentials.
    - Anti-overwrite check: already enrolled users cannot be overwritten.
    - Masked password entry with confirmation.
    - Password length constraints (8-128 characters).
    - Explicit administrative confirmation before write.
    - Atomic commit / rollback on error.
    - Zero credential leakage to stdout, stderr, or shell history.

    Returns:
        0 on success, 1 on validation error, operator abort, or database exception.
    """
    clean_email = email.strip().lower()
    if not clean_email:
        stderr.write("Error: An email address must be provided.\n")
        return 1

    # 1. Verify user exists
    stmt = select(User).where(User.email == clean_email)
    user = session.execute(stmt).scalar_one_or_none()
    if not user:
        stderr.write(f"Error: User with email '{clean_email}' not found.\n")
        return 1

    # 2. Anti-overwrite check: forbid re-enrolling already authenticated accounts
    if user.hashed_password is not None:
        stderr.write(
            f"Error: User '{clean_email}' already has an enrolled password. Re-enrollment prohibited.\n"
        )
        return 1

    # 3. Interactive masked password entry
    try:
        password = password_prompt()
        confirm = confirm_prompt()
    except (KeyboardInterrupt, EOFError):
        stderr.write("\nEnrollment aborted by operator.\n")
        return 1

    # 4. Password validation
    if not password:
        stderr.write("Error: Password cannot be empty.\n")
        return 1

    if len(password) < 8:
        stderr.write("Error: Password must be at least 8 characters long.\n")
        return 1

    if len(password) > 128:
        stderr.write("Error: Password must not exceed 128 characters.\n")
        return 1

    if password != confirm:
        stderr.write("Error: Passwords do not match.\n")
        return 1

    # 5. Explicit operator confirmation prompt
    if confirmation_prompt is None:

        def default_confirm(target_email: str) -> bool:
            try:
                resp = input(
                    f"Are you sure you want to enroll password for user '{target_email}'? [y/N]: "
                )
                return resp.strip().lower() in ("y", "yes")
            except (KeyboardInterrupt, EOFError):
                return False

        confirmation_prompt = default_confirm

    if not confirmation_prompt(user.email or clean_email):
        stdout.write("Enrollment cancelled by operator.\n")
        return 1

    # 6. Atomic commit with Argon2id hash
    try:
        user.hashed_password = hash_password(password)
        session.commit()
        stdout.write(
            f"[SUCCESS] Password enrolled successfully for user '{user.email or clean_email}'.\n"
        )
        return 0
    except Exception as exc:
        session.rollback()
        stderr.write(f"Error committing password enrollment: {exc}\n")
        return 1


def main(
    argv: Sequence[str] | None = None,
    session: Session | None = None,
    stdout: TextIO = sys.stdout,
    stderr: TextIO = sys.stderr,
) -> int:
    """Entrypoint for the administrative password enrollment CLI."""
    parser = argparse.ArgumentParser(
        prog="python -m src.cli.enroll",
        description=(
            "Administrative CLI for securely enrolling initial passwords for legacy user accounts. "
            "Passwords must be entered interactively via masked prompts; CLI arguments for passwords "
            "are strictly prohibited."
        ),
    )
    parser.add_argument(
        "--email",
        required=True,
        help="Target user email address for initial password enrollment.",
    )

    try:
        parsed = parser.parse_args(argv)
    except SystemExit as e:
        return e.code if isinstance(e.code, int) else 1

    own_session = False
    if session is None:
        session = SessionLocal()
        own_session = True

    try:
        return enroll_user(
            email=parsed.email,
            session=session,
            stdout=stdout,
            stderr=stderr,
        )
    finally:
        if own_session:
            session.close()


if __name__ == "__main__":
    sys.exit(main())
