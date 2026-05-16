"""Tests for FlattenEngine and FlattenResult."""
from __future__ import annotations

import pytest

from envoy_local.env_file import EnvFile
from envoy_local.flatten_engine import FlattenEngine, FlattenResult


@pytest.fixture()
def env_file(tmp_path):
    path = tmp_path / ".env"
    path.write_text(
        "APP__DB__HOST=localhost\n"
        "APP__DB__PORT=5432\n"
        "APP__SECRET_KEY=abc123\n"
        "OTHER_VAR=hello\n"
    )
    ef = EnvFile(str(path))
    ef.load()
    return ef


@pytest.fixture()
def engine():
    return FlattenEngine(separator="__")


class TestFlattenResult:
    def test_success_true_when_no_error(self):
        r = FlattenResult(flattened={"KEY": "val"})
        assert r.success is True

    def test_success_false_when_error_set(self):
        r = FlattenResult(error="boom")
        assert r.success is False

    def test_summary_shows_counts(self):
        r = FlattenResult(flattened={"A": "1", "B": "2"}, skipped=["C"])
        assert "2" in r.summary
        assert "1" in r.summary

    def test_summary_shows_error(self):
        r = FlattenResult(error="something broke")
        assert "something broke" in r.summary

    def test_repr_contains_key_info(self):
        r = FlattenResult(flattened={"X": "y"}, skipped=[])
        assert "FlattenResult" in repr(r)
        assert "success=True" in repr(r)


class TestFlattenEngine:
    def test_flattens_all_keys_no_prefix(self, env_file, engine):
        result = engine.flatten(env_file, dry_run=True)
        assert result.success
        # Double-underscore separators replaced with single underscore
        assert "APP_DB_HOST" in result.flattened
        assert "APP_DB_PORT" in result.flattened

    def test_flattens_only_matching_prefix(self, env_file, engine):
        result = engine.flatten(env_file, prefix="APP", dry_run=True)
        assert result.success
        assert all(k.startswith("DB") or k.startswith("SECRET") for k in result.flattened)
        assert "OTHER_VAR" in result.skipped

    def test_strip_prefix_false_keeps_prefix(self, env_file, engine):
        result = engine.flatten(
            env_file, prefix="APP", strip_prefix=False, dry_run=True
        )
        assert result.success
        assert any(k.startswith("APP") for k in result.flattened)

    def test_dry_run_does_not_modify_file(self, env_file, engine):
        original_keys = set(env_file.all().keys())
        engine.flatten(env_file, dry_run=True)
        assert set(env_file.all().keys()) == original_keys

    def test_writes_file_when_not_dry_run(self, env_file, engine):
        result = engine.flatten(env_file, prefix="APP", dry_run=False)
        assert result.success
        reloaded = EnvFile(env_file.path)
        reloaded.load()
        keys = set(reloaded.all().keys())
        # Original nested keys should be gone
        assert "APP__DB__HOST" not in keys

    def test_skipped_keys_preserved_in_result(self, env_file, engine):
        result = engine.flatten(env_file, prefix="APP", dry_run=True)
        assert "OTHER_VAR" in result.skipped

    def test_empty_env_returns_success(self, tmp_path, engine):
        path = tmp_path / "empty.env"
        path.write_text("")
        ef = EnvFile(str(path))
        ef.load()
        result = engine.flatten(ef, dry_run=True)
        assert result.success
        assert result.flattened == {}
