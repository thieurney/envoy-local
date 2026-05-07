"""Tests for cli_template sub-command."""

from __future__ import annotations

import pytest
from pathlib import Path

from envoy_local.cli_template import build_parser, run


@pytest.fixture
def template_file(tmp_path: Path) -> Path:
    p = tmp_path / "app.env.template"
    p.write_text("HOST={{ HOST }}\nPORT={{ PORT }}\n")
    return p


@pytest.fixture
def values_file(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text("HOST=localhost\nPORT=9000\n")
    return p


class TestCliTemplateParser:
    def test_parses_template_and_values(self, template_file, values_file):
        parser = build_parser()
        args = parser.parse_args([str(template_file), "--values", str(values_file)])
        assert args.template == str(template_file)
        assert args.values == str(values_file)

    def test_strict_default_false(self, template_file, values_file):
        parser = build_parser()
        args = parser.parse_args([str(template_file), "--values", str(values_file)])
        assert args.strict is False

    def test_output_default_none(self, template_file, values_file):
        parser = build_parser()
        args = parser.parse_args([str(template_file), "--values", str(values_file)])
        assert args.output is None


class TestCliTemplateRun:
    def test_run_renders_to_stdout(self, template_file, values_file, capsys):
        parser = build_parser()
        args = parser.parse_args([str(template_file), "--values", str(values_file)])
        code = run(args)
        assert code == 0
        captured = capsys.readouterr()
        assert "HOST=localhost" in captured.out
        assert "PORT=9000" in captured.out

    def test_run_writes_output_file(self, template_file, values_file, tmp_path):
        out_file = tmp_path / "rendered.env"
        parser = build_parser()
        args = parser.parse_args([
            str(template_file), "--values", str(values_file),
            "--output", str(out_file)
        ])
        code = run(args)
        assert code == 0
        content = out_file.read_text()
        assert "HOST=localhost" in content

    def test_run_returns_1_for_missing_template(self, values_file, tmp_path):
        parser = build_parser()
        args = parser.parse_args([str(tmp_path / "nope.template"), "--values", str(values_file)])
        assert run(args) == 1

    def test_run_returns_1_for_missing_values(self, template_file, tmp_path):
        parser = build_parser()
        args = parser.parse_args([str(template_file), "--values", str(tmp_path / "nope.env")])
        assert run(args) == 1

    def test_strict_mode_fails_on_unresolved(self, tmp_path):
        tmpl = tmp_path / "t.template"
        tmpl.write_text("KEY={{ MISSING }}\n")
        vals = tmp_path / ".env"
        vals.write_text("OTHER=x\n")
        parser = build_parser()
        args = parser.parse_args([str(tmpl), "--values", str(vals), "--strict"])
        assert run(args) == 1
