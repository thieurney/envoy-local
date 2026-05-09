import pytest
from pathlib import Path

from envoy_local.cli_search import build_parser, run


@pytest.fixture
def env_path(tmp_path):
    p = tmp_path / ".env"
    p.write_text("API_KEY=secret123\nDEBUG=false\nDATABASE_URL=postgres://localhost\n")
    return str(p)


class TestCliSearchParser:
    def test_parses_query_and_files(self, env_path):
        parser = build_parser()
        args = parser.parse_args(["API", env_path])
        assert args.query == "API"
        assert env_path in args.files

    def test_regex_default_false(self, env_path):
        parser = build_parser()
        args = parser.parse_args(["API", env_path])
        assert args.regex is False

    def test_regex_flag(self, env_path):
        parser = build_parser()
        args = parser.parse_args(["API", env_path, "--regex"])
        assert args.regex is True

    def test_mask_secrets_default_false(self, env_path):
        parser = build_parser()
        args = parser.parse_args(["API", env_path])
        assert args.mask_secrets is False

    def test_case_sensitive_default_false(self, env_path):
        parser = build_parser()
        args = parser.parse_args(["API", env_path])
        assert args.case_sensitive is False


class TestCliSearchRun:
    def test_returns_zero_on_match(self, env_path, capsys):
        code = run(["API_KEY", env_path])
        assert code == 0
        out = capsys.readouterr().out
        assert "API_KEY" in out

    def test_returns_zero_no_match(self, env_path, capsys):
        code = run(["NONEXISTENT_KEY", env_path])
        assert code == 0
        out = capsys.readouterr().out
        assert "No matches" in out

    def test_returns_one_on_missing_file(self, capsys):
        code = run(["KEY", "/nonexistent/.env"])
        assert code == 1
        err = capsys.readouterr().err
        assert "not found" in err

    def test_mask_secrets_hides_value(self, env_path, capsys):
        code = run(["API_KEY", env_path, "--mask-secrets"])
        assert code == 0
        out = capsys.readouterr().out
        assert "secret123" not in out

    def test_regex_invalid_returns_one(self, env_path, capsys):
        code = run(["[bad", env_path, "--regex"])
        assert code == 1
        err = capsys.readouterr().err
        assert "Invalid regex" in err

    def test_multiple_files_searched(self, tmp_path, capsys):
        f1 = tmp_path / ".env.a"
        f2 = tmp_path / ".env.b"
        f1.write_text("TOKEN=abc\n")
        f2.write_text("TOKEN=xyz\n")
        code = run(["TOKEN", str(f1), str(f2)])
        assert code == 0
        out = capsys.readouterr().out
        assert "2 match" in out
