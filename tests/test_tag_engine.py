"""Tests for TagEngine and TagResult."""
from __future__ import annotations

import json
import pathlib

import pytest

from envoy_local.env_file import EnvFile
from envoy_local.tag_engine import TagEngine, TagResult


@pytest.fixture()
def env_file(tmp_path: pathlib.Path) -> EnvFile:
    p = tmp_path / ".env"
    p.write_text("DB_HOST=localhost\nDB_PASS=secret\nAPP_ENV=production\n")
    ef = EnvFile(str(p))
    ef.load()
    return ef


@pytest.fixture()
def engine(env_file: EnvFile) -> TagEngine:
    return TagEngine(env_file)


# ---------------------------------------------------------------------------
# TagResult unit tests
# ---------------------------------------------------------------------------

class TestTagResult:
    def test_success_true_when_no_error(self):
        r = TagResult(tagged=["DB_HOST"])
        assert r.success is True

    def test_success_false_when_error_set(self):
        r = TagResult(error="something went wrong")
        assert r.success is False

    def test_summary_shows_tagged_count(self):
        r = TagResult(tagged=["DB_HOST", "APP_ENV"])
        assert "2" in r.summary()

    def test_summary_shows_untagged_count(self):
        r = TagResult(untagged=["DB_PASS"])
        assert "1" in r.summary()

    def test_summary_failure_message(self):
        r = TagResult(error="key not found")
        assert "failed" in r.summary().lower()

    def test_repr_contains_success(self):
        r = TagResult(tagged=["X"])
        assert "success=True" in repr(r)


# ---------------------------------------------------------------------------
# TagEngine tests
# ---------------------------------------------------------------------------

class TestTagEngine:
    def test_add_tag_records_key(self, engine: TagEngine):
        result = engine.add_tag(["DB_HOST"], "infra")
        assert result.success
        assert "DB_HOST" in result.tagged

    def test_tags_for_key_returns_added_tag(self, engine: TagEngine):
        engine.add_tag(["DB_HOST"], "infra")
        assert "infra" in engine.tags_for_key("DB_HOST")

    def test_keys_for_tag_returns_tagged_keys(self, engine: TagEngine):
        engine.add_tag(["DB_HOST", "APP_ENV"], "infra")
        keys = engine.keys_for_tag("infra")
        assert "DB_HOST" in keys
        assert "APP_ENV" in keys

    def test_add_tag_missing_key_returns_error(self, engine: TagEngine):
        result = engine.add_tag(["MISSING_KEY"], "infra")
        assert not result.success
        assert "MISSING_KEY" in (result.error or "")

    def test_remove_tag_works(self, engine: TagEngine):
        engine.add_tag(["DB_PASS"], "secret")
        result = engine.remove_tag(["DB_PASS"], "secret")
        assert result.success
        assert "DB_PASS" in result.untagged
        assert "secret" not in engine.tags_for_key("DB_PASS")

    def test_remove_nonexistent_tag_is_noop(self, engine: TagEngine):
        result = engine.remove_tag(["DB_HOST"], "nonexistent")
        assert result.success
        assert result.untagged == []

    def test_dry_run_does_not_persist(self, engine: TagEngine, tmp_path: pathlib.Path):
        engine.add_tag(["DB_HOST"], "infra", dry_run=True)
        tag_file = pathlib.Path(engine._tag_path)
        assert not tag_file.exists()

    def test_tags_persisted_to_sidecar_file(self, engine: TagEngine, tmp_path: pathlib.Path):
        engine.add_tag(["APP_ENV"], "config")
        tag_file = pathlib.Path(engine._tag_path)
        assert tag_file.exists()
        data = json.loads(tag_file.read_text())
        assert "config" in data.get("APP_ENV", [])

    def test_duplicate_tag_not_added_twice(self, engine: TagEngine):
        engine.add_tag(["DB_HOST"], "infra")
        engine.add_tag(["DB_HOST"], "infra")
        assert engine.tags_for_key("DB_HOST").count("infra") == 1
