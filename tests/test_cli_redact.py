"""Tests for the redact CLI command."""

import pytest
from envoy_local.cli_redact import build_parser, run


@pytest.fixture
def env_path(tmp_path):
    p = tmp_path / ".env"
    p.write_text("DB_PASSWORD=secret\nAPI_KEY=abc123\nAPP_NAME=myapp\n")
    return str(p)


class TestCliRedactParser:
    def test_parses_env_file_and_keys(self):
        parser = build_parser()
        args = parser.parse_args(["/path/.env", "DB_PASSWORD", "API_KEY"])
        assert args.env_file == "/path/.env"
        assert args.keys == ["DB_PASSWORD", "API_KEY"]

    def test_default_placeholder(self):
        parser = build_parser()
        args = parser.parse_args(["/path/.env", "KEY"])
        assert args.placeholder == "***REDACTED***"

    def test_custom_placeholder(self):
        parser = build_parser()
        args = parser.parse_args(["/path/.env", "KEY", "--placeholder", "[HIDDEN]"])
        assert args.placeholder == "[HIDDEN]"

    def test_dry_run_default_false(self):
        parser = build_parser()
        args = parser.parse_args(["/path/.env", "KEY"])
        assert args.dry_run is False

    def test_dry_run_flag(self):
        parser = build_parser()
        args = parser.parse_args(["/path/.env", "KEY", "--dry-run"])
        assert args.dry_run is True

    def test_pattern_flag(self):
        parser = build_parser()
        args = parser.parse_args(["/path/.env", "--pattern", "SECRET"])
        assert args.pattern == "SECRET"


class TestCliRedactRun:
    def test_run_redacts_key(self, env_path):
        exit_code = run([env_path, "DB_PASSWORD"])
        assert exit_code == 0

    def test_run_with_pattern(self, env_path):
        exit_code = run([env_path, "--pattern", "password"])
        assert exit_code == 0

    def test_run_dry_run_does_not_write(self, env_path):
        import pathlib
        original = pathlib.Path(env_path).read_text()
        run([env_path, "DB_PASSWORD", "--dry-run"])
        assert pathlib.Path(env_path).read_text() == original

    def test_run_skips_missing_key_gracefully(self, env_path):
        exit_code = run([env_path, "NONEXISTENT_KEY"])
        assert exit_code == 0
