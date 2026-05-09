"""Tests for CompareEngine and CompareResult."""
import pytest
from unittest.mock import MagicMock
from envoy_local.compare_engine import CompareEngine, CompareResult, CompareEntry


@pytest.fixture
def left_env():
    env = MagicMock()
    env.keys.return_value = ["DB_HOST", "DB_PASS", "APP_ENV"]
    env.get = lambda k, default=None: {
        "DB_HOST": "localhost",
        "DB_PASS": "secret123",
        "APP_ENV": "development",
    }.get(k, default)
    return env


@pytest.fixture
def right_env():
    env = MagicMock()
    env.keys.return_value = ["DB_HOST", "DB_PASS", "NEW_KEY"]
    env.get = lambda k, default=None: {
        "DB_HOST": "prod-db",
        "DB_PASS": "secret123",
        "NEW_KEY": "value",
    }.get(k, default)
    return env


@pytest.fixture
def engine():
    return CompareEngine()


class TestCompareEntry:
    def test_is_same_when_values_equal(self):
        e = CompareEntry(key="K", left_value="v", right_value="v")
        assert e.is_same is True

    def test_is_not_same_when_values_differ(self):
        e = CompareEntry(key="K", left_value="a", right_value="b")
        assert e.is_same is False

    def test_status_only_left(self):
        e = CompareEntry(key="K", left_value="v", right_value=None)
        assert e.status == "only_left"

    def test_status_only_right(self):
        e = CompareEntry(key="K", left_value=None, right_value="v")
        assert e.status == "only_right"

    def test_status_equal(self):
        e = CompareEntry(key="K", left_value="x", right_value="x")
        assert e.status == "equal"

    def test_status_differs(self):
        e = CompareEntry(key="K", left_value="x", right_value="y")
        assert e.status == "differs"

    def test_repr_contains_key_and_status(self):
        e = CompareEntry(key="MY_KEY", left_value="a", right_value="b")
        assert "MY_KEY" in repr(e)
        assert "differs" in repr(e)


class TestCompareResult:
    def test_has_differences_false_when_all_equal(self):
        entries = [CompareEntry("K", "v", "v")]
        result = CompareResult(entries=entries)
        assert result.has_differences is False

    def test_has_differences_true_when_any_differ(self):
        entries = [CompareEntry("K", "a", "b")]
        result = CompareResult(entries=entries)
        assert result.has_differences is True

    def test_differing_keys_returns_correct_keys(self):
        entries = [
            CompareEntry("K1", "same", "same"),
            CompareEntry("K2", "a", "b"),
        ]
        result = CompareResult(entries=entries)
        assert result.differing_keys == ["K2"]

    def test_summary_contains_labels(self):
        result = CompareResult(entries=[], left_label="dev", right_label="prod")
        assert "dev" in result.summary()
        assert "prod" in result.summary()


class TestCompareEngine:
    def test_detects_differing_values(self, engine, left_env, right_env):
        result = engine.compare(left_env, right_env)
        assert "DB_HOST" in result.differing_keys

    def test_equal_values_not_in_differing_keys(self, engine, left_env, right_env):
        result = engine.compare(left_env, right_env)
        assert "DB_PASS" not in result.differing_keys

    def test_missing_key_in_right_detected(self, engine, left_env, right_env):
        result = engine.compare(left_env, right_env)
        app_entry = next(e for e in result.entries if e.key == "APP_ENV")
        assert app_entry.status == "only_left"

    def test_new_key_in_right_detected(self, engine, left_env, right_env):
        result = engine.compare(left_env, right_env)
        new_entry = next(e for e in result.entries if e.key == "NEW_KEY")
        assert new_entry.status == "only_right"

    def test_mask_secrets_applied(self, left_env, right_env):
        masked_engine = CompareEngine(mask_secrets=True)
        result = masked_engine.compare(left_env, right_env)
        pass_entry = next(e for e in result.entries if e.key == "DB_PASS")
        assert pass_entry.left_value != "secret123" or pass_entry.right_value != "secret123"
