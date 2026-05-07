"""Tests for TemplateEngine."""

from __future__ import annotations

import pytest

from envoy_local.template_engine import TemplateEngine, TemplateRenderResult


@pytest.fixture
def engine() -> TemplateEngine:
    return TemplateEngine()


class TestTemplateRenderResult:
    def test_is_complete_when_no_missing(self):
        result = TemplateRenderResult(rendered="ok", filled_keys=["A"], missing_keys=[])
        assert result.is_complete is True

    def test_is_incomplete_when_missing(self):
        result = TemplateRenderResult(rendered="", filled_keys=[], missing_keys=["SECRET"])
        assert result.is_complete is False

    def test_summary_shows_filled_count(self):
        result = TemplateRenderResult(rendered="", filled_keys=["A", "B"], missing_keys=[])
        assert "Filled: 2" in result.summary()

    def test_summary_shows_missing_keys(self):
        result = TemplateRenderResult(rendered="", filled_keys=[], missing_keys=["FOO", "BAR"])
        assert "FOO" in result.summary()
        assert "BAR" in result.summary()


class TestTemplateEngine:
    def test_replaces_single_placeholder(self, engine):
        result = engine.render("HOST={{ HOST }}", {"HOST": "localhost"})
        assert result.rendered == "HOST=localhost"

    def test_replaces_multiple_placeholders(self, engine):
        tmpl = "DB_HOST={{ DB_HOST }}\nDB_PORT={{ DB_PORT }}"
        result = engine.render(tmpl, {"DB_HOST": "127.0.0.1", "DB_PORT": "5432"})
        assert "DB_HOST=127.0.0.1" in result.rendered
        assert "DB_PORT=5432" in result.rendered

    def test_leaves_unresolved_placeholder_intact(self, engine):
        result = engine.render("KEY={{ MISSING }}", {})
        assert "{{ MISSING }}" in result.rendered
        assert "MISSING" in result.missing_keys

    def test_filled_keys_recorded(self, engine):
        result = engine.render("A={{ A }}&B={{ B }}", {"A": "1", "B": "2"})
        assert "A" in result.filled_keys
        assert "B" in result.filled_keys

    def test_strict_mode_raises_on_missing(self):
        strict_engine = TemplateEngine(strict=True)
        with pytest.raises(ValueError, match="Unresolved"):
            strict_engine.render("KEY={{ MISSING }}", {})

    def test_strict_mode_passes_when_all_resolved(self):
        strict_engine = TemplateEngine(strict=True)
        result = strict_engine.render("KEY={{ A }}", {"A": "val"})
        assert result.is_complete

    def test_extract_placeholders_returns_unique_keys(self, engine):
        tmpl = "{{ A }}={{ A }}&{{ B }}"
        keys = engine.extract_placeholders(tmpl)
        assert keys == ["A", "B"]

    def test_render_from_file(self, engine, tmp_path):
        tmpl_file = tmp_path / "sample.env.template"
        tmpl_file.write_text("PORT={{ PORT }}\n")
        result = engine.render_from_file(str(tmpl_file), {"PORT": "8080"})
        assert result.rendered == "PORT=8080\n"
        assert result.is_complete
