"""Tests for MergeEngine and MergeResult."""

import pytest
from pathlib import Path
from unittest.mock import patch

from envoy_local.env_file import EnvFile
from envoy_local.merge_engine import MergeEngine, MergeResult, MergeStrategy, MergeConflict


@pytest.fixture
def base_env(tmp_path):
    p = tmp_path / "base.env"
    p.write_text("APP_NAME=myapp\nDB_HOST=localhost\nSECRET=base_secret\n")
    env = EnvFile(p)
    env.load()
    return env


@pytest.fixture
def target_env(tmp_path):
    p = tmp_path / "target.env"
    p.write_text("APP_NAME=myapp\nDB_HOST=remotehost\nNEW_KEY=newval\n")
    env = EnvFile(p)
    env.load()
    return env


class TestMergeResult:
    def test_has_conflicts_false_when_empty(self):
        r = MergeResult()
        assert r.has_conflicts is False

    def test_has_conflicts_true_when_present(self):
        conflict = MergeConflict("KEY", "a", "b", "a")
        r = MergeResult(conflicts=[conflict])
        assert r.has_conflicts is True

    def test_summary_no_conflicts(self):
        r = MergeResult(merged={"A": "1", "B": "2"}, added_keys=["B"])
        summary = r.summary()
        assert "2 keys" in summary
        assert "1 added" in summary

    def test_summary_with_conflicts(self):
        conflict = MergeConflict("KEY", "a", "b", "a")
        r = MergeResult(
            merged={"KEY": "a"},
            conflicts=[conflict],
            strategy=MergeStrategy.BASE_WINS,
        )
        assert "base_wins" in r.summary()


class TestMergeEngine:
    def test_base_keys_preserved(self, base_env, target_env):
        engine = MergeEngine()
        result = engine.merge(base_env, target_env)
        assert result.merged["SECRET"] == "base_secret"

    def test_new_keys_added_from_target(self, base_env, target_env):
        engine = MergeEngine()
        result = engine.merge(base_env, target_env)
        assert "NEW_KEY" in result.merged
        assert result.merged["NEW_KEY"] == "newval"
        assert "NEW_KEY" in result.added_keys

    def test_conflict_detected_on_differing_values(self, base_env, target_env):
        engine = MergeEngine()
        result = engine.merge(base_env, target_env)
        conflict_keys = [c.key for c in result.conflicts]
        assert "DB_HOST" in conflict_keys

    def test_base_wins_strategy_keeps_base_value(self, base_env, target_env):
        engine = MergeEngine(strategy=MergeStrategy.BASE_WINS)
        result = engine.merge(base_env, target_env)
        assert result.merged["DB_HOST"] == "localhost"

    def test_target_wins_strategy_uses_target_value(self, base_env, target_env):
        engine = MergeEngine(strategy=MergeStrategy.TARGET_WINS)
        result = engine.merge(base_env, target_env)
        assert result.merged["DB_HOST"] == "remotehost"

    def test_no_conflict_when_values_equal(self, base_env, target_env):
        engine = MergeEngine()
        result = engine.merge(base_env, target_env)
        conflict_keys = [c.key for c in result.conflicts]
        assert "APP_NAME" not in conflict_keys

    def test_union_strategy_adds_all_keys(self, base_env, target_env):
        engine = MergeEngine(strategy=MergeStrategy.UNION)
        result = engine.merge(base_env, target_env)
        assert "SECRET" in result.merged
        assert "NEW_KEY" in result.merged
