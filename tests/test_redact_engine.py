"""Tests for RedactEngine and RedactResult."""

import pytest
from unittest.mock import MagicMock
from envoy_local.redact_engine import RedactEngine, RedactResult, REDACT_PLACEHOLDER
from envoy_local.env_file import EnvFile


@pytest.fixture
def env_file(tmp_path):
    path = tmp_path / ".env"
    path.write_text(
        "DB_PASSWORD=secret\nAPI_KEY=abc123\nAPP_NAME=myapp\nSECRET_TOKEN=xyz\n"
    )
    ef = EnvFile(str(path))
    ef.load()
    return ef


@pytest.fixture
def engine():
    return RedactEngine()


class TestRedactResult:
    def test_success_true_when_no_error(self):
        r = RedactResult(redacted_keys=["DB_PASSWORD"])
        assert r.success is True

    def test_success_false_when_error_set(self):
        r = RedactResult(error="something went wrong")
        assert r.success is False

    def test_summary_shows_redacted_count(self):
        r = RedactResult(redacted_keys=["A", "B"])
        assert "2" in r.summary

    def test_summary_shows_skipped_count(self):
        r = RedactResult(redacted_keys=["A"], skipped_keys=["MISSING"])
        assert "skipped" in r.summary

    def test_summary_shows_error_on_failure(self):
        r = RedactResult(error="disk full")
        assert "disk full" in r.summary

    def test_repr_contains_key_info(self):
        r = RedactResult(redacted_keys=["KEY"])
        assert "KEY" in repr(r)


class TestRedactEngine:
    def test_redacts_existing_key(self, env_file, engine):
        result = engine.redact(env_file, ["DB_PASSWORD"], save=False)
        assert "DB_PASSWORD" in result.redacted_keys
        assert env_file.get("DB_PASSWORD") == REDACT_PLACEHOLDER

    def test_skips_missing_key(self, env_file, engine):
        result = engine.redact(env_file, ["NONEXISTENT"], save=False)
        assert "NONEXISTENT" in result.skipped_keys
        assert result.redacted_keys == []

    def test_redacts_multiple_keys(self, env_file, engine):
        result = engine.redact(env_file, ["DB_PASSWORD", "API_KEY"], save=False)
        assert len(result.redacted_keys) == 2
        assert env_file.get("API_KEY") == REDACT_PLACEHOLDER

    def test_custom_placeholder(self, env_file):
        custom_engine = RedactEngine(placeholder="[hidden]")
        custom_engine.redact(env_file, ["DB_PASSWORD"], save=False)
        assert env_file.get("DB_PASSWORD") == "[hidden]"

    def test_redact_pattern_matches_keys(self, env_file, engine):
        result = engine.redact_pattern(env_file, "secret", save=False)
        assert "SECRET_TOKEN" in result.redacted_keys

    def test_redact_pattern_case_insensitive(self, env_file, engine):
        result = engine.redact_pattern(env_file, "PASSWORD", save=False)
        assert "DB_PASSWORD" in result.redacted_keys

    def test_saves_file_when_save_true(self, env_file, engine):
        env_file.save = MagicMock()
        engine.redact(env_file, ["API_KEY"], save=True)
        env_file.save.assert_called_once()

    def test_no_save_on_dry_run(self, env_file, engine):
        env_file.save = MagicMock()
        engine.redact(env_file, ["API_KEY"], save=False)
        env_file.save.assert_not_called()
