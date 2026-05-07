"""Tests for ExportEngine."""

import json
import pytest
from unittest.mock import MagicMock
from envoy_local.export_engine import ExportEngine
from envoy_local.secret_mask import SecretMasker


@pytest.fixture()
def env_file():
    mock = MagicMock()
    mock.all.return_value = [
        ("APP_NAME", "myapp"),
        ("SECRET_KEY", "supersecret"),
        ("DEBUG", "true"),
    ]
    return mock


@pytest.fixture()
def engine():
    return ExportEngine()


class TestExportEngine:
    def test_dotenv_format_produces_quoted_values(self, engine, env_file):
        result = engine.export(env_file, fmt="dotenv")
        assert 'APP_NAME="myapp"' in result
        assert 'DEBUG="true"' in result

    def test_json_format_is_valid_json(self, engine, env_file):
        result = engine.export(env_file, fmt="json")
        parsed = json.loads(result)
        assert parsed["APP_NAME"] == "myapp"
        assert parsed["DEBUG"] == "true"

    def test_shell_format_uses_export(self, engine, env_file):
        result = engine.export(env_file, fmt="shell")
        assert "export APP_NAME='myapp'" in result
        assert "export DEBUG='true'" in result

    def test_mask_secrets_replaces_secret_values(self, engine, env_file):
        result = engine.export(env_file, fmt="dotenv", mask_secrets=True)
        assert "supersecret" not in result
        assert "SECRET_KEY" in result

    def test_unsupported_format_raises_value_error(self, engine, env_file):
        with pytest.raises(ValueError, match="Unsupported format"):
            engine.export(env_file, fmt="xml")

    def test_dotenv_escapes_double_quotes(self, engine):
        mock = MagicMock()
        mock.all.return_value = [("MSG", 'say "hello"')]
        result = engine.export(mock, fmt="dotenv")
        assert 'MSG="say \\"hello\\""' in result

    def test_shell_escapes_single_quotes(self, engine):
        mock = MagicMock()
        mock.all.return_value = [("MSG", "it's fine")]
        result = engine.export(mock, fmt="shell")
        assert "export MSG='it'\"'\"'s fine'" in result

    def test_json_all_keys_present(self, engine, env_file):
        result = engine.export(env_file, fmt="json")
        parsed = json.loads(result)
        assert set(parsed.keys()) == {"APP_NAME", "SECRET_KEY", "DEBUG"}
