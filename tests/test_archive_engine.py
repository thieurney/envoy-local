"""Tests for ArchiveEngine and ArchiveResult."""

from __future__ import annotations

import zipfile
from pathlib import Path

import pytest

from envoy_local.archive_engine import ArchiveEngine, ArchiveResult
from envoy_local.env_file import EnvFile


@pytest.fixture()
def env_file(tmp_path: Path) -> EnvFile:
    p = tmp_path / ".env"
    p.write_text("DB_HOST=localhost\nDB_PASS=secret\nAPP_ENV=production\n")
    ef = EnvFile(str(p))
    ef.load()
    return ef


@pytest.fixture()
def engine(tmp_path: Path) -> ArchiveEngine:
    return ArchiveEngine(tmp_path / "archives")


class TestArchiveResult:
    def test_success_true_when_no_error(self):
        r = ArchiveResult(key_count=3)
        assert r.success is True

    def test_success_false_when_error_set(self):
        r = ArchiveResult(error="boom")
        assert r.success is False

    def test_summary_on_success(self, tmp_path):
        r = ArchiveResult(
            archive_path=tmp_path / "env_20240101.zip",
            source_path=tmp_path / ".env",
            key_count=2,
        )
        s = r.summary()
        assert "2 key(s)" in s
        assert "env_20240101.zip" in s

    def test_summary_on_failure(self):
        r = ArchiveResult(error="permission denied")
        assert "permission denied" in r.summary()

    def test_repr_contains_key_info(self):
        r = ArchiveResult(key_count=5)
        assert "key_count=5" in repr(r)
        assert "success=True" in repr(r)


class TestArchiveEngine:
    def test_archive_creates_zip(self, env_file, engine, tmp_path):
        result = engine.archive(env_file)
        assert result.success
        assert result.archive_path is not None
        assert result.archive_path.exists()
        assert result.archive_path.suffix == ".zip"

    def test_archive_key_count_matches(self, env_file, engine):
        result = engine.archive(env_file)
        assert result.key_count == 3

    def test_archive_label_in_filename(self, env_file, engine):
        result = engine.archive(env_file, label="staging")
        assert "staging" in result.archive_path.name

    def test_zip_contains_env_and_meta(self, env_file, engine):
        result = engine.archive(env_file)
        with zipfile.ZipFile(result.archive_path, "r") as zf:
            names = zf.namelist()
        assert "env.txt" in names
        assert "meta.json" in names

    def test_list_archives_returns_newest_first(self, env_file, engine):
        engine.archive(env_file, label="first")
        engine.archive(env_file, label="second")
        archives = engine.list_archives()
        assert len(archives) == 2
        # newest first — second archive should be index 0
        assert "second" in archives[0].name

    def test_extract_returns_correct_keys(self, env_file, engine):
        result = engine.archive(env_file)
        data = engine.extract(result.archive_path)
        assert data["DB_HOST"] == "localhost"
        assert data["APP_ENV"] == "production"

    def test_storage_dir_created_automatically(self, env_file, tmp_path):
        new_dir = tmp_path / "deep" / "nested" / "archives"
        eng = ArchiveEngine(new_dir)
        result = eng.archive(env_file)
        assert result.success
        assert new_dir.exists()
