"""Tests for the cli_pin module."""

from __future__ import annotations

import pytest

from envoy_local.cli_pin import build_parser, run


@pytest.fixture()
def env_path(tmp_path):
    p = tmp_path / ".env"
    p.write_text("TOKEN=abc\nSECRET=xyz\n")
    return str(p)


class TestCliPinParser:
    def test_parses_env_file_and_keys(self):
        parser = build_parser()
        args = parser.parse_args(["/tmp/.env", "TOKEN", "SECRET"])
        assert args.env_file == "/tmp/.env"
        assert args.keys == ["TOKEN", "SECRET"]

    def test_unpin_flag_default_false(self):
        parser = build_parser()
        args = parser.parse_args(["/tmp/.env", "TOKEN"])
        assert args.unpin is False

    def test_unpin_flag_sets_true(self):
        parser = build_parser()
        args = parser.parse_args(["/tmp/.env", "TOKEN", "--unpin"])
        assert args.unpin is True

    def test_list_flag_default_false(self):
        parser = build_parser()
        args = parser.parse_args(["/tmp/.env", "TOKEN"])
        assert args.list is False

    def test_list_and_unpin_are_mutually_exclusive(self):
        parser = build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["/tmp/.env", "TOKEN", "--list", "--unpin"])


class TestCliPinRun:
    def test_run_pin_exits_zero(self, env_path):
        assert run([env_path, "TOKEN"]) == 0

    def test_run_pin_missing_key_exits_zero(self, env_path):
        # missing keys are skipped, not an error
        assert run([env_path, "DOES_NOT_EXIST"]) == 0

    def test_run_list_exits_zero(self, env_path):
        run([env_path, "TOKEN"])  # pin first
        assert run([env_path, "TOKEN", "--list"]) == 0

    def test_run_unpin_exits_zero(self, env_path):
        run([env_path, "TOKEN"])  # pin first
        assert run([env_path, "TOKEN", "--unpin"]) == 0

    def test_run_bad_file_exits_nonzero(self, tmp_path):
        bad = str(tmp_path / "nonexistent.env")
        assert run([bad, "TOKEN"]) != 0
