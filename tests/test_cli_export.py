"""Tests for the export CLI subcommand."""

import json
import pytest
from pathlib import Path
from envoy_local.cli_export import build_parser, run


@pytest.fixture()
def env_path(tmp_path) -> Path:
    p = tmp_path / ".env"
    p.write_text('APP_NAME="myapp"\nSECRET_KEY="topsecret"\nDEBUG="false"\n')
    return p


class TestCliExportParser:
    def test_default_format_is_dotenv(self, env_path):
        parser = build_parser()
        args = parser.parse_args([str(env_path)])
        assert args.format == "dotenv"

    def test_format_flag_json(self, env_path):
        parser = build_parser()
        args = parser.parse_args([str(env_path), "--format", "json"])
        assert args.format == "json"

    def test_mask_secrets_default_false(self, env_path):
        parser = build_parser()
        args = parser.parse_args([str(env_path)])
        assert args.mask_secrets is False

    def test_mask_secrets_flag(self, env_path):
        parser = build_parser()
        args = parser.parse_args([str(env_path), "--mask-secrets"])
        assert args.mask_secrets is True


class TestCliExportRun:
    def test_run_dotenv_returns_zero(self, env_path, capsys):
        parser = build_parser()
        args = parser.parse_args([str(env_path)])
        code = run(args)
        assert code == 0

    def test_run_json_output_is_valid(self, env_path, capsys):
        parser = build_parser()
        args = parser.parse_args([str(env_path), "--format", "json"])
        run(args)
        captured = capsys.readouterr()
        parsed = json.loads(captured.out)
        assert "APP_NAME" in parsed

    def test_run_missing_file_returns_one(self, tmp_path, capsys):
        parser = build_parser()
        args = parser.parse_args([str(tmp_path / "nonexistent.env")])
        code = run(args)
        assert code == 1

    def test_run_writes_to_output_file(self, env_path, tmp_path):
        out_file = tmp_path / "out.json"
        parser = build_parser()
        args = parser.parse_args(
            [str(env_path), "--format", "json", "--output", str(out_file)]
        )
        code = run(args)
        assert code == 0
        assert out_file.exists()
        parsed = json.loads(out_file.read_text())
        assert parsed["APP_NAME"] == "myapp"
