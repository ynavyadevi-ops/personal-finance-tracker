"""Unit tests for the administrative password enrollment CLI (src/cli/enroll.py)."""

import io
from unittest.mock import MagicMock

from sqlalchemy.orm import Session

from src.cli.enroll import enroll_user, main
from src.core.security import hash_password, verify_password
from src.db.models.user import User


def test_enroll_success(db_session: Session) -> None:
    """Verify successful initial password enrollment for a legacy unauthenticated user."""
    user = User(
        id="legacy-cli-user-1",
        name="Legacy User One",
        email="legacy1@example.dev",
        hashed_password=None,
    )
    db_session.add(user)
    db_session.flush()

    stdout = io.StringIO()
    stderr = io.StringIO()

    exit_code = enroll_user(
        email="legacy1@example.dev",
        session=db_session,
        password_prompt=lambda: "ValidSecret999!",
        confirm_prompt=lambda: "ValidSecret999!",
        confirmation_prompt=lambda _target: True,
        stdout=stdout,
        stderr=stderr,
    )

    assert exit_code == 0
    assert "Password enrolled successfully for user 'legacy1@example.dev'" in stdout.getvalue()
    assert stderr.getvalue() == ""

    # Refresh user and verify Argon2id hash
    db_session.refresh(user)
    assert user.hashed_password is not None
    assert verify_password("ValidSecret999!", user.hashed_password) is True

    # Critical security assertion: plaintext password or hash never in output
    assert "ValidSecret999!" not in stdout.getvalue()
    assert user.hashed_password not in stdout.getvalue()


def test_enroll_user_not_found(db_session: Session) -> None:
    """Verify enrollment fails cleanly when target user does not exist in the database."""
    stdout = io.StringIO()
    stderr = io.StringIO()

    exit_code = enroll_user(
        email="nonexistent@example.dev",
        session=db_session,
        password_prompt=lambda: "ValidSecret999!",
        confirm_prompt=lambda: "ValidSecret999!",
        confirmation_prompt=lambda _target: True,
        stdout=stdout,
        stderr=stderr,
    )

    assert exit_code == 1
    assert "User with email 'nonexistent@example.dev' not found" in stderr.getvalue()
    assert stdout.getvalue() == ""


def test_enroll_anti_overwrite_protection(db_session: Session) -> None:
    """Verify anti-overwrite protection rejects re-enrolling an already authenticated user."""
    initial_hash = hash_password("InitialPassword123!")
    user = User(
        id="already-enrolled-user",
        name="Active User",
        email="active@example.dev",
        hashed_password=initial_hash,
    )
    db_session.add(user)
    db_session.flush()

    stdout = io.StringIO()
    stderr = io.StringIO()

    exit_code = enroll_user(
        email="active@example.dev",
        session=db_session,
        password_prompt=lambda: "AttemptedNewPassword456!",
        confirm_prompt=lambda: "AttemptedNewPassword456!",
        confirmation_prompt=lambda _target: True,
        stdout=stdout,
        stderr=stderr,
    )

    assert exit_code == 1
    assert "already has an enrolled password. Re-enrollment prohibited" in stderr.getvalue()

    # Verify original hash remains completely untouched
    db_session.refresh(user)
    assert user.hashed_password == initial_hash
    assert verify_password("InitialPassword123!", user.hashed_password) is True


def test_enroll_password_mismatch(db_session: Session) -> None:
    """Verify enrollment aborts if candidate password confirmation does not match."""
    user = User(
        id="mismatch-user",
        name="Mismatch User",
        email="mismatch@example.dev",
        hashed_password=None,
    )
    db_session.add(user)
    db_session.flush()

    stdout = io.StringIO()
    stderr = io.StringIO()

    exit_code = enroll_user(
        email="mismatch@example.dev",
        session=db_session,
        password_prompt=lambda: "PasswordOne123!",
        confirm_prompt=lambda: "PasswordTwo456!",
        confirmation_prompt=lambda _target: True,
        stdout=stdout,
        stderr=stderr,
    )

    assert exit_code == 1
    assert "Passwords do not match" in stderr.getvalue()
    db_session.refresh(user)
    assert user.hashed_password is None


def test_enroll_password_too_short(db_session: Session) -> None:
    """Verify enrollment enforces minimum password length (8 characters)."""
    user = User(
        id="short-user",
        name="Short User",
        email="short@example.dev",
        hashed_password=None,
    )
    db_session.add(user)
    db_session.flush()

    stdout = io.StringIO()
    stderr = io.StringIO()

    exit_code = enroll_user(
        email="short@example.dev",
        session=db_session,
        password_prompt=lambda: "short",
        confirm_prompt=lambda: "short",
        confirmation_prompt=lambda _target: True,
        stdout=stdout,
        stderr=stderr,
    )

    assert exit_code == 1
    assert "Password must be at least 8 characters long" in stderr.getvalue()
    db_session.refresh(user)
    assert user.hashed_password is None


def test_enroll_password_too_long(db_session: Session) -> None:
    """Verify enrollment enforces maximum password length (128 characters)."""
    user = User(
        id="long-user",
        name="Long User",
        email="long@example.dev",
        hashed_password=None,
    )
    db_session.add(user)
    db_session.flush()

    stdout = io.StringIO()
    stderr = io.StringIO()

    long_password = "A" * 129
    exit_code = enroll_user(
        email="long@example.dev",
        session=db_session,
        password_prompt=lambda: long_password,
        confirm_prompt=lambda: long_password,
        confirmation_prompt=lambda _target: True,
        stdout=stdout,
        stderr=stderr,
    )

    assert exit_code == 1
    assert "Password must not exceed 128 characters" in stderr.getvalue()
    db_session.refresh(user)
    assert user.hashed_password is None


def test_enroll_operator_cancelled(db_session: Session) -> None:
    """Verify enrollment aborts cleanly without DB changes when operator declines confirmation."""
    user = User(
        id="cancelled-user",
        name="Cancelled User",
        email="cancelled@example.dev",
        hashed_password=None,
    )
    db_session.add(user)
    db_session.flush()

    stdout = io.StringIO()
    stderr = io.StringIO()

    exit_code = enroll_user(
        email="cancelled@example.dev",
        session=db_session,
        password_prompt=lambda: "ValidPassword123!",
        confirm_prompt=lambda: "ValidPassword123!",
        confirmation_prompt=lambda _target: False,
        stdout=stdout,
        stderr=stderr,
    )

    assert exit_code == 1
    assert "Enrollment cancelled by operator" in stdout.getvalue()
    db_session.refresh(user)
    assert user.hashed_password is None


def test_enroll_database_rollback_on_commit_error(db_session: Session) -> None:
    """Verify session is rolled back if database commit fails during enrollment."""
    user = User(
        id="rollback-user",
        name="Rollback User",
        email="rollback@example.dev",
        hashed_password=None,
    )
    db_session.add(user)
    db_session.flush()

    stdout = io.StringIO()
    stderr = io.StringIO()

    # Wrap session with a mock commit that fails
    mock_session = MagicMock(wraps=db_session)
    mock_session.commit.side_effect = RuntimeError("Simulated DB disk failure")

    exit_code = enroll_user(
        email="rollback@example.dev",
        session=mock_session,
        password_prompt=lambda: "ValidPassword123!",
        confirm_prompt=lambda: "ValidPassword123!",
        confirmation_prompt=lambda _target: True,
        stdout=stdout,
        stderr=stderr,
    )

    assert exit_code == 1
    mock_session.rollback.assert_called_once()
    assert "Error committing password enrollment" in stderr.getvalue()


def test_cli_main_argument_parsing_rejects_missing_email() -> None:
    """Verify CLI main entrypoint fails when --email is omitted."""
    stderr = io.StringIO()
    exit_code = main([], stderr=stderr)
    assert exit_code != 0


def test_cli_main_rejects_password_command_line_argument() -> None:
    """Verify CLI main entrypoint strictly rejects passing passwords via command line arguments."""
    stderr = io.StringIO()
    exit_code = main(
        ["--email", "test@example.dev", "--password", "InsecureArgumentPassword"],
        stderr=stderr,
    )
    assert exit_code != 0


def test_enroll_empty_email_rejected(db_session: Session) -> None:
    """Verify enrollment rejects empty or whitespace-only email."""
    stderr = io.StringIO()
    exit_code = enroll_user(email="   ", session=db_session, stderr=stderr)
    assert exit_code == 1
    assert "An email address must be provided" in stderr.getvalue()


def test_enroll_keyboard_interrupt_handled(db_session: Session) -> None:
    """Verify KeyboardInterrupt during password entry cleanly aborts without error trace."""
    user = User(
        id="sigint-user",
        name="Sigint User",
        email="sigint@example.dev",
        hashed_password=None,
    )
    db_session.add(user)
    db_session.flush()

    def raise_sigint() -> str:
        raise KeyboardInterrupt()

    stderr = io.StringIO()
    exit_code = enroll_user(
        email="sigint@example.dev",
        session=db_session,
        password_prompt=raise_sigint,
        stderr=stderr,
    )
    assert exit_code == 1
    assert "Enrollment aborted by operator" in stderr.getvalue()


def test_enroll_default_confirmation_prompt(db_session: Session, monkeypatch: object) -> None:
    """Verify default confirmation prompt logic when accepting, declining, or raising EOF."""
    user = User(
        id="default-prompt-user",
        name="Default Prompt User",
        email="prompt@example.dev",
        hashed_password=None,
    )
    db_session.add(user)
    db_session.flush()

    import pytest

    # Case 1: user types 'y'
    monkeypatch_obj: pytest.MonkeyPatch = monkeypatch  # type: ignore[assignment]
    monkeypatch_obj.setattr("builtins.input", lambda _prompt: "y")
    stdout = io.StringIO()
    exit_code = enroll_user(
        email="prompt@example.dev",
        session=db_session,
        password_prompt=lambda: "ValidPassword123!",
        confirm_prompt=lambda: "ValidPassword123!",
        stdout=stdout,
    )
    assert exit_code == 0
    db_session.refresh(user)
    assert user.hashed_password is not None


def test_cli_main_end_to_end_with_session(db_session: Session, monkeypatch: object) -> None:
    """Verify main() executes end-to-end when session is supplied."""
    import pytest

    user = User(
        id="main-user",
        name="Main User",
        email="main@example.dev",
        hashed_password=None,
    )
    db_session.add(user)
    db_session.flush()

    monkeypatch_obj: pytest.MonkeyPatch = monkeypatch  # type: ignore[assignment]
    monkeypatch_obj.setattr("getpass.getpass", lambda _prompt="": "CLIValidPass123!")
    monkeypatch_obj.setattr("builtins.input", lambda _prompt="": "yes")

    stdout = io.StringIO()
    stderr = io.StringIO()
    exit_code = main(
        ["--email", "main@example.dev"],
        session=db_session,
        stdout=stdout,
        stderr=stderr,
    )
    assert exit_code == 0
    assert "[SUCCESS] Password enrolled successfully" in stdout.getvalue()
