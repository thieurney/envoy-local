"""Tests for InjectEngine and InjectResult."""
from __future__ import annotations

import os
import pytest

from envoy_local.env_file import EnvFile
from envoy_local.inject_engine import InjectEngine, InjectResult


@pytest.fixture()
def env_file(tmp_path):
    p = tmp_path / ".env"
    p.write_text("APP_NAME=envoy\nSECRET_KEY=supersecret\nDEBUG=false\n")
    ef = EnvFile(str(p))
    ef.load()
    return ef


@pytest.fixture()
def engine():
    return InjectEngine()


class TestInjectResult:
    def test_success_true_when_no_error(self):
        r = InjectResult(injected=["A", "B"])
        assert r.success is True

    def test_success_false_when_error_set(self):
        r = InjectResult(error="boom")
        assert r.success is False

    def test_summary_shows_injected_count(self):
        r = InjectResult(injected=["A", "B"])
        assert "2" in r.summary()

    def test_summary_shows_skipped_when_present(self):
        r = InjectResult(injected=["A"], skipped=["B", "C"])
        assert "skipped" in r.summary()
        assert "2" in r.summary()

    def test_summary_shows_error(self):
        r = InjectResult(error="disk full")
        assert "disk full" in r.summary()


class TestInjectEngine:
    def test_build_env_merges_with_os_environ(self, env_file, engine):
        merged = engine.build_env(env_file)
        assert merged["APP_NAME"] == "envoy"
        assert "PATH" in merged  # os.environ key preserved

    def test_build_env_skips_existing_by_default(self, env_file, engine, monkeypatch):
        monkeypatch.setenv("APP_NAME", "original")
        merged = engine.build_env(env_file, overwrite=False)
        assert merged["APP_NAME"] == "original"

    def test_build_env_overwrites_when_flag_set(self, env_file, engine, monkeypatch):
        monkeypatch.setenv("APP_NAME", "original")
        merged = engine.build_env(env_file, overwrite=True)
        assert merged["APP_NAME"] == "envoy"

    def test_inject_sets_os_environ(self, env_file, engine, monkeypatch):
        monkeypatch.delenv("APP_NAME", raising=False)
        result = engine.inject(env_file)
        assert result.success
        assert os.environ.get("APP_NAME") == "envoy"

    def test_inject_skips_existing_without_overwrite(self, env_file, engine, monkeypatch):
        monkeypatch.setenv("APP_NAME", "kept")
        result = engine.inject(env_file, overwrite=False)
        assert "APP_NAME" in result.skipped
        assert os.environ["APP_NAME"] == "kept"

    def test_inject_overwrites_when_flag_set(self, env_file, engine, monkeypatch):
        monkeypatch.setenv("APP_NAME", "old")
        result = engine.inject(env_file, overwrite=True)
        assert "APP_NAME" in result.injected
        assert os.environ["APP_NAME"] == "envoy"

    def test_export_shell_contains_export_statements(self, env_file, engine):
        output = engine.export_shell(env_file)
        assert 'export APP_NAME="envoy"' in output
        assert 'export DEBUG="false"' in output

    def test_export_shell_masks_secrets(self, env_file, engine):
        output = engine.export_shell(env_file, mask_secrets=True)
        assert "supersecret" not in output
        assert "SECRET_KEY" in output
