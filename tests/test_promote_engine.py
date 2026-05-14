"""Tests for PromoteEngine and PromoteResult."""

import pytest
from unittest.mock import MagicMock
from envoy_local.promote_engine import PromoteEngine, PromoteResult
from envoy_local.env_file import EnvFile


def _make_env(data: dict) -> MagicMock:
    env = MagicMock(spec=EnvFile)
    env.all.return_value = dict(data)
    return env


class TestPromoteResult:
    def test_success_true_when_no_error(self):
        result = PromoteResult(promoted={"A": "1"})
        assert result.success is True

    def test_success_false_when_error_set(self):
        result = PromoteResult(error="something went wrong")
        assert result.success is False

    def test_summary_shows_promoted_count(self):
        result = PromoteResult(promoted={"A": "1", "B": "2"})
        assert "2 key(s) promoted" in result.summary()

    def test_summary_shows_overwritten(self):
        result = PromoteResult(promoted={"A": "1"}, overwritten=["A"])
        assert "1 overwritten" in result.summary()

    def test_summary_shows_skipped(self):
        result = PromoteResult(promoted={}, skipped=["X", "Y"])
        assert "2 skipped" in result.summary()

    def test_summary_on_failure(self):
        result = PromoteResult(error="disk error")
        assert "disk error" in result.summary()

    def test_repr_contains_key_info(self):
        result = PromoteResult(promoted={"K": "v"}, skipped=["Z"])
        r = repr(result)
        assert "promoted=1" in r
        assert "skipped=1" in r


class TestPromoteEngine:
    def test_promotes_all_keys_by_default(self):
        source = _make_env({"A": "1", "B": "2"})
        target = _make_env({})
        engine = PromoteEngine()
        result = engine.promote(source, target, dry_run=True)
        assert set(result.promoted.keys()) == {"A", "B"}
        assert result.skipped == []

    def test_promotes_only_specified_keys(self):
        source = _make_env({"A": "1", "B": "2", "C": "3"})
        target = _make_env({})
        engine = PromoteEngine(keys=["A", "C"])
        result = engine.promote(source, target, dry_run=True)
        assert set(result.promoted.keys()) == {"A", "C"}
        assert "B" not in result.promoted

    def test_skips_missing_source_keys(self):
        source = _make_env({"A": "1"})
        target = _make_env({})
        engine = PromoteEngine(keys=["A", "MISSING"])
        result = engine.promote(source, target, dry_run=True)
        assert "MISSING" in result.skipped
        assert "A" in result.promoted

    def test_skips_existing_target_keys_without_overwrite(self):
        source = _make_env({"A": "new"})
        target = _make_env({"A": "old"})
        engine = PromoteEngine(overwrite=False)
        result = engine.promote(source, target, dry_run=True)
        assert "A" in result.skipped
        assert "A" not in result.promoted

    def test_overwrites_existing_keys_when_flag_set(self):
        source = _make_env({"A": "new"})
        target = _make_env({"A": "old"})
        engine = PromoteEngine(overwrite=True)
        result = engine.promote(source, target, dry_run=True)
        assert "A" in result.promoted
        assert "A" in result.overwritten

    def test_dry_run_does_not_call_save(self):
        source = _make_env({"A": "1"})
        target = _make_env({})
        engine = PromoteEngine()
        engine.promote(source, target, dry_run=True)
        target.save.assert_not_called()

    def test_save_called_when_not_dry_run(self):
        source = _make_env({"A": "1"})
        target = _make_env({})
        engine = PromoteEngine()
        engine.promote(source, target, dry_run=False)
        target.save.assert_called_once()
