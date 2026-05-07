"""Tests for the watch CLI entry point."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from envoy_local.cli_watch import build_parser, run


@pytest.fixture
def env_path(tmp_path: Path) -> str:
    p = tmp_path / ".env"
    p.write_text("KEY=value\n")
    return str(p)


class TestCliWatchParser:
    def test_parses_single_file(self, env_path: str) -> None:
        parser = build_parser()
        args = parser.parse_args([env_path])
        assert args.files == [env_path]

    def test_parses_multiple_files(self, env_path: str) -> None:
        parser = build_parser()
        args = parser.parse_args([env_path, env_path])
        assert len(args.files) == 2

    def test_default_interval(self, env_path: str) -> None:
        parser = build_parser()
        args = parser.parse_args([env_path])
        assert args.interval == 2.0

    def test_custom_interval(self, env_path: str) -> None:
        parser = build_parser()
        args = parser.parse_args([env_path, "--interval", "5"])
        assert args.interval == 5.0

    def test_once_default_false(self, env_path: str) -> None:
        parser = build_parser()
        args = parser.parse_args([env_path])
        assert args.once is False

    def test_once_flag(self, env_path: str) -> None:
        parser = build_parser()
        args = parser.parse_args([env_path, "--once"])
        assert args.once is True


class TestCliWatchRun:
    def test_once_exits_without_loop(self, env_path: str, capsys) -> None:
        run([env_path, "--once"])
        out = capsys.readouterr().out
        assert "Watching" in out

    def test_once_prints_modified_event(self, env_path: str, capsys) -> None:
        # Modify after registering by patching poll to return a modified event
        from envoy_local.watch_engine import WatchEvent, WatchResult

        fake_result = WatchResult(events=[WatchEvent(path=env_path, kind="modified")])
        with patch("envoy_local.cli_watch.WatchEngine.poll", return_value=fake_result):
            run([env_path, "--once"])
        out = capsys.readouterr().out
        assert "MODIFIED" in out
        assert env_path in out
