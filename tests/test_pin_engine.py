"""Tests for PinEngine and PinResult."""

from __future__ import annotations

import pytest

from envoy_local.env_file import EnvFile
from envoy_local.pin_engine import PIN_COMMENT_MARKER, PinEngine, PinResult


@pytest.fixture()
def env_file(tmp_path):
    path = tmp_path / ".env"
    path.write_text("DB_HOST=localhost\nDB_PASS=secret\nAPI_KEY=abc123\n")
    ef = EnvFile(str(path))
    ef.load()
    return ef


@pytest.fixture()
def engine(env_file):
    return PinEngine(env_file)


class TestPinResult:
    def test_success_true_when_no_error(self):
        r = PinResult(pinned=["A"], skipped=[])
        assert r.success is True

    def test_success_false_when_error_set(self):
        r = PinResult(error="boom")
        assert r.success is False

    def test_summary_shows_pinned_count(self):
        r = PinResult(pinned=["A", "B"], skipped=[])
        assert "2 key(s) pinned" in r.summary()

    def test_summary_shows_skipped_count(self):
        r = PinResult(pinned=[], skipped=["X"])
        assert "1 key(s) skipped" in r.summary()

    def test_summary_failure_message(self):
        r = PinResult(error="disk full")
        assert "disk full" in r.summary()

    def test_summary_nothing_to_pin(self):
        r = PinResult()
        assert r.summary() == "Nothing to pin."

    def test_repr_contains_success(self):
        r = PinResult(pinned=["K"])
        assert "success=True" in repr(r)


class TestPinEngine:
    def test_pin_existing_key_returns_success(self, engine):
        result = engine.pin(["DB_HOST"])
        assert result.success
        assert "DB_HOST" in result.pinned

    def test_pin_missing_key_goes_to_skipped(self, engine):
        result = engine.pin(["MISSING_KEY"])
        assert result.success
        assert "MISSING_KEY" in result.skipped
        assert "MISSING_KEY" not in result.pinned

    def test_pin_multiple_keys(self, engine):
        result = engine.pin(["DB_HOST", "API_KEY"])
        assert len(result.pinned) == 2
        assert result.skipped == []

    def test_list_pinned_returns_pinned_keys(self, engine):
        engine.pin(["DB_PASS"])
        pinned = engine.list_pinned()
        assert "DB_PASS" in pinned

    def test_list_pinned_empty_initially(self, engine):
        assert engine.list_pinned() == []

    def test_unpin_removes_marker(self, engine):
        engine.pin(["API_KEY"])
        assert "API_KEY" in engine.list_pinned()
        result = engine.unpin(["API_KEY"])
        assert result.success
        assert "API_KEY" not in engine.list_pinned()

    def test_unpin_missing_key_skipped(self, engine):
        result = engine.unpin(["GHOST"])
        assert result.success
        assert "GHOST" in result.skipped

    def test_pin_saves_file(self, engine, env_file, tmp_path):
        engine.pin(["DB_HOST"])
        reloaded = EnvFile(env_file.path)
        reloaded.load()
        meta = reloaded.metadata().get("DB_HOST", {})
        assert PIN_COMMENT_MARKER in meta.get("comment", "")
