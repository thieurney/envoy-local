"""Tests for CloneEngine and CloneResult."""

import pytest
from pathlib import Path

from envoy_local.env_file import EnvFile
from envoy_local.clone_engine import CloneEngine, CloneResult


@pytest.fixture
def source_env(tmp_path: Path) -> EnvFile:
    p = tmp_path / "source.env"
    p.write_text("APP_NAME=myapp\nDB_PASS=secret\nDEBUG=true\n")
    env = EnvFile(p)
    env.load()
    return env


@pytest.fixture
def engine(source_env: EnvFile) -> CloneEngine:
    return CloneEngine(source_env)


class TestCloneResult:
    def test_success_true_when_no_error(self):
        r = CloneResult(source=Path("a.env"), destination=Path("b.env"), copied_keys=["K"])
        assert r.success is True

    def test_success_false_when_error_set(self):
        r = CloneResult(source=Path("a.env"), destination=Path("b.env"), error="oops")
        assert r.success is False

    def test_summary_on_success(self):
        r = CloneResult(
            source=Path("a.env"),
            destination=Path("b.env"),
            copied_keys=["A", "B"],
            skipped_keys=["C"],
        )
        s = r.summary()
        assert "2 key(s)" in s
        assert "skipped 1" in s

    def test_summary_on_failure(self):
        r = CloneResult(source=Path("a.env"), destination=Path("b.env"), error="bad path")
        assert "failed" in r.summary().lower()


class TestCloneEngine:
    def test_clones_all_keys(self, engine: CloneEngine, tmp_path: Path):
        dest = tmp_path / "dest.env"
        result = engine.clone(dest)
        assert result.success
        assert set(result.copied_keys) == {"APP_NAME", "DB_PASS", "DEBUG"}
        assert result.skipped_keys == []

    def test_destination_file_is_created(self, engine: CloneEngine, tmp_path: Path):
        dest = tmp_path / "dest.env"
        engine.clone(dest)
        assert dest.exists()

    def test_cloned_values_match_source(self, engine: CloneEngine, tmp_path: Path):
        dest = tmp_path / "dest.env"
        engine.clone(dest)
        cloned = EnvFile(dest)
        cloned.load()
        assert cloned.get("APP_NAME") == "myapp"
        assert cloned.get("DB_PASS") == "secret"

    def test_include_keys_filters_output(self, engine: CloneEngine, tmp_path: Path):
        dest = tmp_path / "dest.env"
        result = engine.clone(dest, include_keys=["APP_NAME", "DEBUG"])
        assert result.success
        assert result.copied_keys == ["APP_NAME", "DEBUG"]
        assert "DB_PASS" in result.skipped_keys

    def test_exclude_keys_removes_specified(self, engine: CloneEngine, tmp_path: Path):
        dest = tmp_path / "dest.env"
        result = engine.clone(dest, exclude_keys=["DB_PASS"])
        assert result.success
        assert "DB_PASS" not in result.copied_keys
        assert "DB_PASS" in result.skipped_keys

    def test_overwrite_false_blocks_existing_dest(self, engine: CloneEngine, tmp_path: Path):
        dest = tmp_path / "dest.env"
        dest.write_text("EXISTING=1\n")
        result = engine.clone(dest, overwrite=False)
        assert not result.success
        assert "already exists" in result.error

    def test_overwrite_true_replaces_existing_dest(self, engine: CloneEngine, tmp_path: Path):
        dest = tmp_path / "dest.env"
        dest.write_text("EXISTING=1\n")
        result = engine.clone(dest, overwrite=True)
        assert result.success
