"""Tests for the filter CLI entry-point."""
from __future__ import annotations

import pytest

from envoy_local.cli_filter import build_parser, run


@pytest.fixture()
def env_path(tmp_path):
    p = tmp_path / ".env"
    p.write_text(
        "DB_HOST=localhost\n"
        "DB_PORT=5432\n"
        "APP_NAME=myapp\n"
    )
    return str(p)


class TestCliFilterParser:
    def test_parses_pattern(self, env_path):
        parser = build_parser()
        args = parser.parse_args([env_path, "--pattern", r"^DB_"])
        assert args.pattern == r"^DB_"
        assert args.prefix is None

    def test_parses_prefix(self, env_path):
        parser = build_parser()
        args = parser.parse_args([env_path, "--prefix", "APP_"])
        assert args.prefix == "APP_"
        assert args.pattern is None

    def test_invert_default_false(self, env_path):
        parser = build_parser()
        args = parser.parse_args([env_path, "--prefix", "DB_"])
        assert args.invert is False

    def test_invert_flag_sets_true(self, env_path):
        parser = build_parser()
        args = parser.parse_args([env_path, "--prefix", "DB_", "--invert"])
        assert args.invert is True

    def test_show_excluded_default_false(self, env_path):
        parser = build_parser()
        args = parser.parse_args([env_path, "--prefix", "DB_"])
        assert args.show_excluded is False

    def test_pattern_and_prefix_mutually_exclusive(self, env_path):
        parser = build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args([env_path, "--pattern", r"DB", "--prefix", "DB_"])


class TestCliFilterRun:
    def test_run_by_prefix_returns_zero(self, env_path, capsys):
        code = run([env_path, "--prefix", "DB_"])
        assert code == 0
        out = capsys.readouterr().out
        assert "DB_HOST" in out
        assert "APP_NAME" not in out

    def test_run_by_pattern_returns_zero(self, env_path, capsys):
        code = run([env_path, "--pattern", r"^APP_"])
        assert code == 0
        out = capsys.readouterr().out
        assert "APP_NAME" in out

    def test_run_invalid_regex_returns_one(self, env_path, capsys):
        code = run([env_path, "--pattern", r"[bad"])
        assert code == 1
        err = capsys.readouterr().err
        assert "Error" in err

    def test_show_excluded_prints_excluded_section(self, env_path, capsys):
        code = run([env_path, "--prefix", "DB_", "--show-excluded"])
        assert code == 0
        out = capsys.readouterr().out
        assert "Excluded keys" in out
        assert "APP_NAME" in out

    def test_invert_shows_non_matching_keys(self, env_path, capsys):
        code = run([env_path, "--prefix", "DB_", "--invert"])
        assert code == 0
        out = capsys.readouterr().out
        assert "APP_NAME" in out
        assert "DB_HOST" not in out
