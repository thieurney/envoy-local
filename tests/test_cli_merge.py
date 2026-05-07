"""Tests for the CLI merge command."""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from envoy_local.cli_merge import build_parser, run


@pytest.fixture
def base_env(tmp_path):
    p = tmp_path / "base.env"
    p.write_text("APP=base\nSHARED=base_val\n")
    return p


@pytest.fixture
def target_env(tmp_path):
    p = tmp_path / "target.env"
    p.write_text("APP=target\nNEW=newval\n")
    return p


class TestCliMergeParser:
    def test_parses_base_and_target(self, base_env, target_env):
        parser = build_parser()
        args = parser.parse_args([str(base_env), str(target_env)])
        assert args.base == str(base_env)
        assert args.target == str(target_env)

    def test_default_strategy_is_base_wins(self, base_env, target_env):
        parser = build_parser()
        args = parser.parse_args([str(base_env), str(target_env)])
        assert args.strategy == "base_wins"

    def test_strategy_flag_target_wins(self, base_env, target_env):
        parser = build_parser()
        args = parser.parse_args([str(base_env), str(target_env), "--strategy", "target_wins"])
        assert args.strategy == "target_wins"

    def test_show_conflicts_default_false(self, base_env, target_env):
        parser = build_parser()
        args = parser.parse_args([str(base_env), str(target_env)])
        assert args.show_conflicts is False

    def test_output_flag(self, base_env, target_env, tmp_path):
        out = tmp_path / "merged.env"
        parser = build_parser()
        args = parser.parse_args([str(base_env), str(target_env), "--output", str(out)])
        assert args.output == str(out)


class TestCliMergeRun:
    def test_run_exits_on_missing_base(self, tmp_path, target_env, capsys):
        parser = build_parser()
        args = parser.parse_args([str(tmp_path / "missing.env"), str(target_env)])
        with pytest.raises(SystemExit) as exc:
            run(args)
        assert exc.value.code == 1

    def test_run_exits_on_missing_target(self, base_env, tmp_path, capsys):
        parser = build_parser()
        args = parser.parse_args([str(base_env), str(tmp_path / "missing.env")])
        with pytest.raises(SystemExit) as exc:
            run(args)
        assert exc.value.code == 1

    def test_run_prints_summary(self, base_env, target_env, capsys):
        parser = build_parser()
        args = parser.parse_args([str(base_env), str(target_env)])
        run(args)
        captured = capsys.readouterr()
        assert "keys" in captured.out

    def test_run_writes_output_file(self, base_env, target_env, tmp_path):
        out = tmp_path / "merged.env"
        parser = build_parser()
        args = parser.parse_args([str(base_env), str(target_env), "--output", str(out)])
        run(args)
        assert out.exists()
        content = out.read_text()
        assert "NEW" in content
