"""Tests for GroupEngine and GroupResult."""

import pytest

from envoy_local.env_file import EnvFile
from envoy_local.group_engine import GroupEngine, GroupResult


@pytest.fixture
def env_file(tmp_path):
    p = tmp_path / ".env"
    p.write_text("DB_HOST=localhost\nDB_PORT=5432\nAPI_KEY=secret\nDEBUG=true\n")
    ef = EnvFile(str(p))
    ef.load()
    return ef


@pytest.fixture
def engine(env_file):
    return GroupEngine(env_file)


class TestGroupResult:
    def test_success_true_when_no_error(self):
        r = GroupResult(group_name="db", keys=["DB_HOST"])
        assert r.success is True

    def test_success_false_when_error_set(self):
        r = GroupResult(group_name="db", error="something went wrong")
        assert r.success is False

    def test_summary_shows_key_count(self):
        r = GroupResult(group_name="db", keys=["DB_HOST", "DB_PORT"])
        assert "2 key(s)" in r.summary
        assert "db" in r.summary

    def test_summary_shows_missing_keys(self):
        r = GroupResult(group_name="db", keys=["DB_HOST"], missing_keys=["DB_PASS"])
        assert "missing" in r.summary
        assert "DB_PASS" in r.summary

    def test_summary_shows_error_on_failure(self):
        r = GroupResult(group_name="x", error="Group 'x' not found")
        assert "failed" in r.summary

    def test_repr_contains_group_name(self):
        r = GroupResult(group_name="api", keys=["API_KEY"])
        assert "api" in repr(r)


class TestGroupEngine:
    def test_define_group_success(self, engine):
        result = engine.define_group("db", ["DB_HOST", "DB_PORT"])
        assert result.success
        assert "DB_HOST" in result.keys

    def test_define_group_reports_missing_keys(self, engine):
        result = engine.define_group("db", ["DB_HOST", "DB_PASS"])
        assert result.success  # still succeeds, just reports missing
        assert "DB_PASS" in result.missing_keys

    def test_define_group_empty_name_fails(self, engine):
        result = engine.define_group("", ["DB_HOST"])
        assert not result.success

    def test_define_group_empty_keys_fails(self, engine):
        result = engine.define_group("db", [])
        assert not result.success

    def test_get_group_returns_present_keys(self, engine):
        engine.define_group("db", ["DB_HOST", "DB_PORT"])
        result = engine.get_group("db")
        assert result.success
        assert set(result.keys) == {"DB_HOST", "DB_PORT"}

    def test_get_group_unknown_group_fails(self, engine):
        result = engine.get_group("nonexistent")
        assert not result.success

    def test_list_groups(self, engine):
        engine.define_group("db", ["DB_HOST"])
        engine.define_group("api", ["API_KEY"])
        groups = engine.list_groups()
        assert "db" in groups
        assert "api" in groups

    def test_filter_env_returns_values(self, engine):
        engine.define_group("db", ["DB_HOST", "DB_PORT"])
        filtered = engine.filter_env("db")
        assert filtered == {"DB_HOST": "localhost", "DB_PORT": "5432"}

    def test_filter_env_unknown_group_returns_none(self, engine):
        assert engine.filter_env("ghost") is None

    def test_remove_group_returns_true_when_exists(self, engine):
        engine.define_group("db", ["DB_HOST"])
        assert engine.remove_group("db") is True
        assert "db" not in engine.list_groups()

    def test_remove_group_returns_false_when_missing(self, engine):
        assert engine.remove_group("nope") is False
