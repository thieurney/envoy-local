"""Tests for WatchEngine and related dataclasses."""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from envoy_local.watch_engine import WatchEngine, WatchEvent, WatchResult


@pytest.fixture
def tmp_env(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text("KEY=value\n")
    return p


@pytest.fixture
def engine(tmp_env: Path) -> WatchEngine:
    e = WatchEngine()
    e.register(str(tmp_env))
    return e


class TestWatchEvent:
    def test_repr_contains_kind_and_path(self) -> None:
        ev = WatchEvent(path="/a/.env", kind="modified")
        assert "modified" in repr(ev)
        assert "/a/.env" in repr(ev)

    def test_timestamp_is_set_automatically(self) -> None:
        before = time.time()
        ev = WatchEvent(path="x", kind="created")
        assert ev.timestamp >= before


class TestWatchResult:
    def test_has_changes_false_when_empty(self) -> None:
        r = WatchResult()
        assert r.has_changes is False

    def test_has_changes_true_with_events(self) -> None:
        r = WatchResult(events=[WatchEvent(path="x", kind="modified")])
        assert r.has_changes is True

    def test_summary_no_changes(self) -> None:
        assert "No changes" in WatchResult().summary()

    def test_summary_lists_events(self) -> None:
        r = WatchResult(events=[WatchEvent(path="/a/.env", kind="modified")])
        assert "MODIFIED" in r.summary()
        assert "/a/.env" in r.summary()


class TestWatchEngine:
    def test_no_event_when_file_unchanged(self, engine: WatchEngine, tmp_env: Path) -> None:
        result = engine.poll()
        assert not result.has_changes

    def test_detects_modification(self, engine: WatchEngine, tmp_env: Path) -> None:
        tmp_env.write_text("KEY=changed\n")
        result = engine.poll()
        assert result.has_changes
        assert result.events[0].kind == "modified"

    def test_detects_deletion(self, engine: WatchEngine, tmp_env: Path) -> None:
        tmp_env.unlink()
        result = engine.poll()
        assert result.has_changes
        assert result.events[0].kind == "deleted"

    def test_detects_creation_of_new_file(self, tmp_path: Path) -> None:
        p = tmp_path / "new.env"
        e = WatchEngine()
        e.register(str(p))  # does not exist yet
        p.write_text("X=1\n")
        result = e.poll()
        assert result.has_changes
        assert result.events[0].kind == "created"

    def test_callback_is_invoked_on_change(self, engine: WatchEngine, tmp_env: Path) -> None:
        received: list[WatchEvent] = []
        engine.on_change(received.append)
        tmp_env.write_text("KEY=new\n")
        engine.poll()
        assert len(received) == 1
        assert received[0].kind == "modified"

    def test_multiple_files_tracked(self, tmp_path: Path) -> None:
        a = tmp_path / "a.env"
        b = tmp_path / "b.env"
        a.write_text("A=1\n")
        b.write_text("B=2\n")
        e = WatchEngine()
        e.register(str(a))
        e.register(str(b))
        b.write_text("B=changed\n")
        result = e.poll()
        assert result.has_changes
        paths = [ev.path for ev in result.events]
        assert str(b) in paths
        assert str(a) not in paths
