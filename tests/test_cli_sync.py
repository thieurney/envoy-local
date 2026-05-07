"""Tests for the sync CLI command."""

import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from envoy_local.cli_sync import build_parser, run


@pytest.fixture
def source_env(tmp_path):
    f = tmp_path / "source.env"
    f.write_text("KEY=value\nSECRET_KEY=topsecret\n")
    return str(f)


@pytest.fixture
def registry_with_project(tmp_path, source_env):
    from envoy_local.project_registry import ProjectRegistry
    reg_path = str(tmp_path / "registry.json")
    reg = ProjectRegistry(reg_path)
    target = str(tmp_path / "proj" / ".env")
    Path(target).parent.mkdir()
    Path(target).write_text("KEY=old\n")
    reg.register("proj", target)
    return reg_path, target


class TestCliSyncParser:
    def test_parses_source(self):
        parser = build_parser()
        args = parser.parse_args(["myfile.env"])
        assert args.source == "myfile.env"

    def test_dry_run_default_false(self):
        parser = build_parser()
        args = parser.parse_args(["myfile.env"])
        assert args.dry_run is False

    def test_dry_run_flag(self):
        parser = build_parser()
        args = parser.parse_args(["myfile.env", "--dry-run"])
        assert args.dry_run is True

    def test_show_secrets_flag(self):
        parser = build_parser()
        args = parser.parse_args(["myfile.env", "--show-secrets"])
        assert args.show_secrets is True


class TestCliSyncRun:
    def test_run_returns_zero_on_success(self, source_env, registry_with_project, capsys):
        reg_path, target = registry_with_project
        exit_code = run([source_env, "--registry", reg_path])
        assert exit_code == 0

    def test_run_dry_run_prints_would_sync(self, source_env, registry_with_project, capsys):
        reg_path, _ = registry_with_project
        run([source_env, "--dry-run", "--registry", reg_path])
        captured = capsys.readouterr()
        assert "dry-run" in captured.out

    def test_run_masks_secrets(self, source_env, registry_with_project, capsys):
        reg_path, _ = registry_with_project
        run([source_env, "--registry", reg_path])
        captured = capsys.readouterr()
        assert "topsecret" not in captured.out

    def test_run_show_secrets(self, source_env, registry_with_project, capsys):
        reg_path, _ = registry_with_project
        run([source_env, "--show-secrets", "--registry", reg_path])
        captured = capsys.readouterr()
        # SECRET_KEY is modified, show-secrets means no masking label used
        assert "***" not in captured.out
