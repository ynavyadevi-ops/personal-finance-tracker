"""Unit tests for Pydantic Settings configuration."""

import pytest

from src.core.config import Settings


def test_settings_default_values() -> None:
    """Verify default configuration attributes."""
    cfg = Settings()
    assert cfg.APP_NAME == "Personal Finance Tracker"
    assert cfg.APP_VERSION == "0.1.0"
    assert cfg.ENVIRONMENT in {"development", "testing", "staging", "production"}
    assert "sqlite" in cfg.DATABASE_URL
    assert len(cfg.cors_origins_list) >= 1


def test_settings_invalid_environment() -> None:
    """Verify ValueError is raised on unsupported environment name."""
    with pytest.raises(ValueError, match="ENVIRONMENT must be one of"):
        Settings(ENVIRONMENT="invalid_env_name")
