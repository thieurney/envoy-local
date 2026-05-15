"""Tests for FilterEngine and FilterResult."""
from __future__ import annotations

import pytest

from envoy_local.env_file import EnvFile
from envoy_local.filter_engine import FilterEngine, FilterResult


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def env_file(tmp_path):
    p = tmp_path / ".env"
    p.write_text(
        "DB_HOST=localhost\n"
        "DB_PORT=5432\n"
        "APP_NAME=myapp\n"
        "APP_DEBUG=true\n"
        "SECRET_KEY=s3cr3t\n"
    )
    ef = EnvFile(str(p))
    ef.load()
    return ef


@pytest.fixture()
def engine(env_file):
    return FilterEngine(env_file)


# ---------------------------------------------------------------------------
# FilterResult unit tests
# ---------------------------------------------------------------------------

class TestFilterResult:
    def test_success_true_when_no_error(self):
        r = FilterResult(matched={"A": "1"}, excluded={})
        assert r.success is True

    def test_success_false_when_error_set(self):
        r = FilterResult(matched={}, excluded={}, error="oops")
        assert r.success is False

    def test_summary_shows_counts(self):
        r = FilterResult(matched={"A": "1", "B": "2"}, excluded={"C": "3"})
        summary = r.summary()
        assert "2" in summary
        assert "1" in summary

    def test_summary_shows_error_on_failure(self):
        r = FilterResult(matched={}, excluded={}, error="bad regex")
        assert "bad regex" in r.summary()

    def test_repr_contains_counts(self):
        r = FilterResult(matched={"X": "1"}, excluded={"Y": "2"})
        assert "matched=1" in repr(r)
        assert "excluded=1" in repr(r)


# ---------------------------------------------------------------------------
# FilterEngine.by_prefix
# ---------------------------------------------------------------------------

class TestFilterEngineByPrefix:
    def test_matches_db_prefix(self, engine):
        result = engine.by_prefix("DB_")
        assert set(result.matched.keys()) == {"DB_HOST", "DB_PORT"}

    def test_excluded_contains_rest(self, engine):
        result = engine.by_prefix("DB_")
        assert "APP_NAME" in result.excluded
        assert "SECRET_KEY" in result.excluded

    def test_invert_excludes_prefix(self, engine):
        result = engine.by_prefix("DB_", invert=True)
        assert "DB_HOST" not in result.matched
        assert "APP_NAME" in result.matched

    def test_no_match_returns_empty_matched(self, engine):
        result = engine.by_prefix("NONEXISTENT_")
        assert result.matched == {}
        assert result.success is True


# ---------------------------------------------------------------------------
# FilterEngine.by_pattern
# ---------------------------------------------------------------------------

class TestFilterEngineByPattern:
    def test_matches_keys_with_pattern(self, engine):
        result = engine.by_pattern(r"^APP_")
        assert set(result.matched.keys()) == {"APP_NAME", "APP_DEBUG"}

    def test_invalid_regex_returns_error(self, engine):
        result = engine.by_pattern(r"[invalid")
        assert result.success is False
        assert result.error is not None

    def test_case_sensitive_by_default(self, engine):
        result = engine.by_pattern(r"^app_")
        assert result.matched == {}

    def test_invert_pattern(self, engine):
        result = engine.by_pattern(r"SECRET", invert=True)
        assert "SECRET_KEY" not in result.matched
        assert "DB_HOST" in result.matched


# ---------------------------------------------------------------------------
# FilterEngine.by_predicate
# ---------------------------------------------------------------------------

class TestFilterEngineByPredicate:
    def test_predicate_on_value(self, engine):
        result = engine.by_predicate(lambda _k, v: v.isdigit())
        assert "DB_PORT" in result.matched
        assert "DB_HOST" not in result.matched

    def test_predicate_exception_returns_error(self, engine):
        def bad(_k, _v):
            raise RuntimeError("boom")

        result = engine.by_predicate(bad)
        assert result.success is False
        assert "boom" in result.error
