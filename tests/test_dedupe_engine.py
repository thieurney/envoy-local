"""Tests for DedupeEngine and DedupeResult."""

import pytest

from envoy_local.env_file import EnvFile
from envoy_local.dedupe_engine import DedupeEngine, DedupeResult


@pytest.fixture
def env_file(tmp_path):
    path = tmp_path / ".env"
    path.write_text(
        "HOST=localhost\nPORT=5432\nHOST=remotehost\nDEBUG=true\nPORT=9999\n"
    )
    ef = EnvFile(str(path))
    ef.load()
    return ef


@pytest.fixture
def engine(env_file):
    return DedupeEngine(env_file)


# ---------------------------------------------------------------------------
# DedupeResult unit tests
# ---------------------------------------------------------------------------

class TestDedupeResult:
    def test_success_true_when_no_error(self):
        result = DedupeResult()
        assert result.success is True

    def test_success_false_when_error_set(self):
        result = DedupeResult(error="something went wrong")
        assert result.success is False

    def test_summary_no_duplicates(self):
        result = DedupeResult()
        assert "No duplicate" in result.summary

    def test_summary_with_duplicates_and_removed(self):
        result = DedupeResult(duplicates=["HOST", "PORT"], removed=["HOST", "PORT"])
        assert "2" in result.summary
        assert "removed" in result.summary

    def test_summary_failure(self):
        result = DedupeResult(error="disk full")
        assert "failed" in result.summary.lower()
        assert "disk full" in result.summary

    def test_repr_contains_key_info(self):
        result = DedupeResult(duplicates=["KEY"], removed=["KEY"])
        r = repr(result)
        assert "DedupeResult" in r
        assert "KEY" in r


# ---------------------------------------------------------------------------
# DedupeEngine integration tests
# ---------------------------------------------------------------------------

class TestDedupeEngine:
    def test_find_duplicates_returns_duplicate_keys(self, engine):
        dupes = engine.find_duplicates()
        assert "HOST" in dupes
        assert "PORT" in dupes

    def test_find_duplicates_excludes_unique_keys(self, engine):
        dupes = engine.find_duplicates()
        assert "DEBUG" not in dupes

    def test_dry_run_does_not_modify_file(self, engine, env_file):
        original_keys = list(env_file.keys())
        result = engine.dedupe(dry_run=True)
        assert list(env_file.keys()) == original_keys
        assert result.success is True
        assert len(result.duplicates) == 2
        assert result.removed == []

    def test_dedupe_removes_duplicate_keys(self, engine, env_file):
        result = engine.dedupe(dry_run=False)
        assert result.success is True
        keys = list(env_file.keys())
        assert keys.count("HOST") == 1
        assert keys.count("PORT") == 1

    def test_dedupe_reports_removed_keys(self, engine):
        result = engine.dedupe(dry_run=False)
        assert "HOST" in result.removed or "PORT" in result.removed

    def test_dedupe_no_duplicates_returns_empty(self, tmp_path):
        path = tmp_path / ".env"
        path.write_text("A=1\nB=2\nC=3\n")
        ef = EnvFile(str(path))
        ef.load()
        eng = DedupeEngine(ef)
        result = eng.dedupe()
        assert result.success is True
        assert result.duplicates == []
        assert result.removed == []
