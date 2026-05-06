"""Tests for the DiffEngine module."""

import pytest

from envoy_local.diff_engine import DiffEngine, DiffResult
from envoy_local.env_file import EnvFile


@pytest.fixture
def base_env(tmp_path):
    p = tmp_path / ".env.base"
    p.write_text(
        "APP_NAME=myapp\n"
        "DB_HOST=localhost\n"
        "SECRET_KEY=supersecret\n"
        "DEBUG=true\n"
    )
    ef = EnvFile(str(p))
    ef.load()
    return ef


@pytest.fixture
def target_env(tmp_path):
    p = tmp_path / ".env.target"
    p.write_text(
        "APP_NAME=myapp\n"
        "DB_HOST=remotehost\n"
        "SECRET_KEY=newsecret\n"
        "NEW_VAR=hello\n"
    )
    ef = EnvFile(str(p))
    ef.load()
    return ef


class TestDiffEngine:
    def test_detects_added_keys(self, base_env, target_env):
        engine = DiffEngine(mask_secrets=False)
        result = engine.compare(base_env, target_env)
        assert "NEW_VAR" in result.added
        assert result.added["NEW_VAR"] == "hello"

    def test_detects_removed_keys(self, base_env, target_env):
        engine = DiffEngine(mask_secrets=False)
        result = engine.compare(base_env, target_env)
        assert "DEBUG" in result.removed

    def test_detects_changed_keys(self, base_env, target_env):
        engine = DiffEngine(mask_secrets=False)
        result = engine.compare(base_env, target_env)
        assert "DB_HOST" in result.changed
        old, new = result.changed["DB_HOST"]
        assert old == "localhost"
        assert new == "remotehost"

    def test_detects_unchanged_keys(self, base_env, target_env):
        engine = DiffEngine(mask_secrets=False)
        result = engine.compare(base_env, target_env)
        assert "APP_NAME" in result.unchanged

    def test_has_changes_true(self, base_env, target_env):
        engine = DiffEngine(mask_secrets=False)
        result = engine.compare(base_env, target_env)
        assert result.has_changes is True

    def test_no_changes_identical_files(self, tmp_path):
        content = "APP=test\nDEBUG=false\n"
        for name in (".env.a", ".env.b"):
            p = tmp_path / name
            p.write_text(content)

        ef_a = EnvFile(str(tmp_path / ".env.a"))
        ef_a.load()
        ef_b = EnvFile(str(tmp_path / ".env.b"))
        ef_b.load()

        engine = DiffEngine(mask_secrets=False)
        result = engine.compare(ef_a, ef_b)
        assert result.has_changes is False

    def test_secret_masking_in_diff(self, base_env, target_env):
        engine = DiffEngine(mask_secrets=True)
        result = engine.compare(base_env, target_env)
        old, new = result.changed["SECRET_KEY"]
        assert "supersecret" not in old
        assert "newsecret" not in new

    def test_format_diff_no_changes(self, tmp_path):
        content = "X=1\n"
        for name in (".env.x", ".env.y"):
            (tmp_path / name).write_text(content)
        ef_x = EnvFile(str(tmp_path / ".env.x"))
        ef_x.load()
        ef_y = EnvFile(str(tmp_path / ".env.y"))
        ef_y.load()
        engine = DiffEngine(mask_secrets=False)
        result = engine.compare(ef_x, ef_y)
        assert engine.format_diff(result) == "(no changes)"

    def test_format_diff_contains_symbols(self, base_env, target_env):
        engine = DiffEngine(mask_secrets=False)
        result = engine.compare(base_env, target_env)
        formatted = engine.format_diff(result)
        assert "+" in formatted or "-" in formatted or "~" in formatted

    def test_summary_output(self, base_env, target_env):
        engine = DiffEngine(mask_secrets=False)
        result = engine.compare(base_env, target_env)
        summary = result.summary()
        assert "Added" in summary
        assert "Removed" in summary
        assert "Changed" in summary
