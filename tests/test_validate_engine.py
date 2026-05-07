"""Tests for ValidateEngine and ValidationResult."""

import pytest
from unittest.mock import MagicMock
from envoy_local.validate_engine import ValidateEngine, ValidationResult
from envoy_local.env_file import EnvFile


@pytest.fixture
def env_file(tmp_path):
    p = tmp_path / ".env"
    p.write_text("DB_HOST=localhost\nDB_PORT=5432\nAPI_KEY=secret\nEMPTY_KEY=\n")
    ef = EnvFile(str(p))
    ef.load()
    return ef


class TestValidationResult:
    def test_is_valid_when_no_issues(self):
        result = ValidationResult()
        assert result.is_valid is True

    def test_is_invalid_when_missing_keys(self):
        result = ValidationResult(missing_keys=["FOO"])
        assert result.is_valid is False

    def test_is_invalid_when_empty_keys(self):
        result = ValidationResult(empty_keys=["BAR"])
        assert result.is_valid is False

    def test_summary_all_ok(self):
        result = ValidationResult()
        assert "present" in result.summary()

    def test_summary_shows_missing(self):
        result = ValidationResult(missing_keys=["SECRET"])
        assert "SECRET" in result.summary()
        assert "Missing" in result.summary()

    def test_summary_shows_empty(self):
        result = ValidationResult(empty_keys=["EMPTY_KEY"])
        assert "EMPTY_KEY" in result.summary()
        assert "Empty" in result.summary()

    def test_summary_shows_unexpected(self):
        result = ValidationResult(unexpected_keys=["EXTRA"])
        assert "EXTRA" in result.summary()
        assert "Unexpected" in result.summary()


class TestValidateEngine:
    def test_valid_env_passes(self, env_file):
        engine = ValidateEngine(required_keys=["DB_HOST", "DB_PORT", "API_KEY"])
        result = engine.validate(env_file)
        assert result.is_valid is True

    def test_detects_missing_key(self, env_file):
        engine = ValidateEngine(required_keys=["DB_HOST", "MISSING_KEY"])
        result = engine.validate(env_file)
        assert "MISSING_KEY" in result.missing_keys

    def test_detects_empty_key(self, env_file):
        engine = ValidateEngine(required_keys=["EMPTY_KEY"])
        result = engine.validate(env_file)
        assert "EMPTY_KEY" in result.empty_keys

    def test_no_unexpected_keys_when_allow_extra(self, env_file):
        engine = ValidateEngine(required_keys=["DB_HOST"], allow_extra=True)
        result = engine.validate(env_file)
        assert result.unexpected_keys == []

    def test_detects_unexpected_keys_when_strict(self, env_file):
        engine = ValidateEngine(required_keys=["DB_HOST"], allow_extra=False)
        result = engine.validate(env_file)
        assert len(result.unexpected_keys) > 0
        assert "API_KEY" in result.unexpected_keys

    def test_validate_from_schema_file(self, env_file, tmp_path):
        schema = tmp_path / "schema.txt"
        schema.write_text("# required keys\nDB_HOST\nDB_PORT\n")
        engine = ValidateEngine(required_keys=[])
        result = engine.validate_from_schema_file(str(schema), env_file)
        assert result.is_valid is True
        assert "DB_HOST" in engine.required_keys

    def test_missing_keys_are_sorted(self, env_file):
        engine = ValidateEngine(required_keys=["Z_KEY", "A_KEY", "M_KEY"])
        result = engine.validate(env_file)
        assert result.missing_keys == sorted(result.missing_keys)
