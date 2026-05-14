"""Tests for ConvertEngine and ConvertResult."""

from __future__ import annotations

import json
import pytest

from envoy_local.convert_engine import ConvertEngine, ConvertResult
from envoy_local.env_file import EnvFile


@pytest.fixture()
def env_file(tmp_path):
    p = tmp_path / ".env"
    p.write_text('DB_HOST="localhost"\nDB_PORT="5432"\nSECRET_KEY="abc123"\n')
    ef = EnvFile(str(p))
    ef.load()
    return ef


@pytest.fixture()
def engine(env_file):
    return ConvertEngine(env_file)


class TestConvertResult:
    def test_success_true_when_no_error(self):
        r = ConvertResult(format="json", output="{}", keys_converted=0)
        assert r.success is True

    def test_success_false_when_error_set(self):
        r = ConvertResult(format="xml", output="", error="Unsupported format")
        assert r.success is False

    def test_summary_on_success(self):
        r = ConvertResult(format="json", output="{}", keys_converted=3)
        assert "3" in r.summary()
        assert "json" in r.summary()

    def test_summary_on_failure(self):
        r = ConvertResult(format="xml", output="", error="bad format")
        assert "failed" in r.summary().lower()

    def test_repr_contains_format_and_success(self):
        r = ConvertResult(format="yaml", output="", keys_converted=2)
        assert "yaml" in repr(r)
        assert "True" in repr(r)


class TestConvertEngine:
    def test_json_format_is_valid_json(self, engine):
        result = engine.convert("json")
        assert result.success
        parsed = json.loads(result.output)
        assert parsed["DB_HOST"] == "localhost"

    def test_dotenv_format_has_quoted_values(self, engine):
        result = engine.convert("dotenv")
        assert result.success
        assert 'DB_HOST="localhost"' in result.output

    def test_yaml_format_contains_keys(self, engine):
        result = engine.convert("yaml")
        assert result.success
        assert "DB_HOST" in result.output
        assert "localhost" in result.output

    def test_shell_format_uses_export(self, engine):
        result = engine.convert("shell")
        assert result.success
        assert "export DB_HOST" in result.output

    def test_keys_converted_count_is_correct(self, engine):
        result = engine.convert("json")
        assert result.keys_converted == 3

    def test_unsupported_format_returns_error(self, engine):
        result = engine.convert("xml")
        assert not result.success
        assert "xml" in result.error.lower()

    def test_format_case_insensitive(self, engine):
        result = engine.convert("JSON")
        assert result.success

    def test_empty_env_produces_empty_json(self, tmp_path):
        p = tmp_path / ".env"
        p.write_text("")
        ef = EnvFile(str(p))
        ef.load()
        eng = ConvertEngine(ef)
        result = eng.convert("json")
        assert result.success
        assert json.loads(result.output) == {}
