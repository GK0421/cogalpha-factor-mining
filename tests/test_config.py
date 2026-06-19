"""Tests for configuration management."""

from __future__ import annotations

import pytest
from cogalpha.config import Config, _resolve_env_vars, load_config


def test_load_config_from_example(tmp_path):
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        """
api:
  provider: "openai"
data:
  symbols:
    - X
    - Y
"""
    )
    config = load_config(config_path)
    assert config.api.provider == "openai"
    assert config.data.symbols == ["X", "Y"]
    # Default values should be preserved
    assert config.api.openai.base_url == "https://api.openai.com/v1"
    # Since env var not mocked here, it keeps the literal string
    assert config.api.openai.api_key == "${OPENAI_API_KEY}"


def test_env_var_override(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test123")
    resolved = _resolve_env_vars({"api_key": "${OPENAI_API_KEY}"})
    assert resolved["api_key"] == "sk-test123"

    # When env var is missing, keep literal string
    monkeypatch.delenv("MISSING_KEY", raising=False)
    resolved2 = _resolve_env_vars({"api_key": "${MISSING_KEY}"})
    assert resolved2["api_key"] == "${MISSING_KEY}"


def test_api_key_suppression_in_repr():
    config = Config()
    rep = repr(config)
    assert "***REDACTED***" in rep
    assert "${OPENAI_API_KEY}" not in rep

    str_rep = str(config)
    assert "***REDACTED***" in str_rep
    assert "${OPENAI_API_KEY}" not in str_rep


def test_missing_config_file_raises():
    with pytest.raises(FileNotFoundError):
        load_config("nonexistent_config.yaml")
