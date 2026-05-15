"""Tests for ScopeEngine and ScopeResult."""

from __future__ import annotations

import pytest

from envoy_local.env_file import EnvFile
from envoy_local.scope_engine import ScopeEngine, ScopeResult


@pytest.fixture()
def env_file(tmp_path):
    path = tmp_path / ".env"
    path.write_text(
        "DB_HOST=localhost\n"
        "DB_PORT=5432\n"
        "APP_NAME=envoy\n"
        "APP_ENV=production\n"
        "SECRET_KEY=abc123\n"
    )
    ef = EnvFile(str(path))
    ef.load()
    return ef


@pytest.fixture()
def engine(env_file):
    return ScopeEngine(env_file)


class TestScopeResult:
    def test_success_true_when_no_error(self):
        result = ScopeResult(scoped={"A": "1"}, excluded=[])
        assert result.success is True

    def test_success_false_when_error_set(self):
        result = ScopeResult(error="oops")
        assert result.success is False

    def test_summary_shows_counts(self):
        result = ScopeResult(scoped={"A": "1", "B": "2"}, excluded=["C"])
        summary = result.summary()
        assert "2" in summary
        assert "1" in summary

    def test_summary_shows_error_message(self):
        result = ScopeResult(error="bad prefix")
        assert "bad prefix" in result.summary()


class TestScopeEngineByPrefix:
    def test_returns_matching_keys(self, engine):
        result = engine.by_prefix("DB_")
        assert set(result.scoped.keys()) == {"DB_HOST", "DB_PORT"}

    def test_excluded_contains_non_matching(self, engine):
        result = engine.by_prefix("DB_")
        assert "APP_NAME" in result.excluded
        assert "SECRET_KEY" in result.excluded

    def test_strip_prefix_removes_prefix(self, engine):
        result = engine.by_prefix("DB_", strip_prefix=True)
        assert "HOST" in result.scoped
        assert "PORT" in result.scoped
        assert "DB_HOST" not in result.scoped

    def test_empty_prefix_returns_error(self, engine):
        result = engine.by_prefix("")
        assert result.success is False
        assert result.error is not None

    def test_no_match_returns_empty_scoped(self, engine):
        result = engine.by_prefix("UNKNOWN_")
        assert result.scoped == {}
        assert len(result.excluded) == 5


class TestScopeEngineByPattern:
    def test_returns_matching_keys(self, engine):
        result = engine.by_pattern(r"^DB_")
        assert set(result.scoped.keys()) == {"DB_HOST", "DB_PORT"}

    def test_pattern_matches_substring(self, engine):
        result = engine.by_pattern(r"_KEY$")
        assert "SECRET_KEY" in result.scoped

    def test_invalid_pattern_returns_error(self, engine):
        result = engine.by_pattern(r"[invalid")
        assert result.success is False
        assert "Invalid regex" in result.error

    def test_excluded_contains_non_matching(self, engine):
        result = engine.by_pattern(r"^APP_")
        assert "DB_HOST" in result.excluded
        assert "SECRET_KEY" in result.excluded

    def test_pattern_case_sensitive(self, engine):
        result = engine.by_pattern(r"^db_")
        assert result.scoped == {}
