"""Tests for the SyncEngine and SyncReport."""

import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from envoy_local.sync_engine import SyncEngine, SyncReport, SyncResult
from envoy_local.diff_engine import DiffResult
from envoy_local.env_file import EnvFile
from envoy_local.project_registry import ProjectRegistry


@pytest.fixture
def tmp_registry(tmp_path):
    reg_file = tmp_path / "registry.json"
    registry = ProjectRegistry(str(reg_file))
    return registry


@pytest.fixture
def source_env_file(tmp_path):
    src = tmp_path / "source.env"
    src.write_text("APP_NAME=envoy\nSECRET_KEY=abc123\nDEBUG=true\n")
    return str(src)


@pytest.fixture
def target_env_file(tmp_path):
    tgt = tmp_path / "project_a" / ".env"
    tgt.parent.mkdir()
    tgt.write_text("APP_NAME=old_name\nDEBUG=true\n")
    return str(tgt)


class TestSyncReport:
    def test_summary_string(self):
        diff = DiffResult(added=["A"], removed=[], modified=[], unchanged=[])
        results = [
            SyncResult("p1", "/p1", diff, applied=True),
            SyncResult("p2", "/p2", DiffResult([], [], [], ["X"]), applied=False),
            SyncResult("p3", "/p3", diff, applied=False, error="oops"),
        ]
        report = SyncReport(source="/src.env", results=results)
        assert report.total == 3
        assert report.synced == 1
        assert report.failed == 1
        assert "synced" in report.summary()

    def test_skipped_count(self):
        no_change = DiffResult([], [], [], ["KEY"])
        results = [
            SyncResult("p1", "/p1", no_change, applied=False),
            SyncResult("p2", "/p2", no_change, applied=False),
        ]
        report = SyncReport(source="/src", results=results)
        assert report.skipped == 2


class TestSyncEngine:
    def test_sync_applies_changes(self, tmp_registry, source_env_file, target_env_file):
        tmp_registry.register("project_a", target_env_file)
        engine = SyncEngine(tmp_registry)
        report = engine.sync(source_env_file, dry_run=False)

        assert report.total == 1
        result = report.results[0]
        assert result.applied is True
        assert result.error is None
        content = Path(target_env_file).read_text()
        assert "SECRET_KEY=abc123" in content

    def test_dry_run_does_not_write(self, tmp_registry, source_env_file, target_env_file):
        original = Path(target_env_file).read_text()
        tmp_registry.register("project_a", target_env_file)
        engine = SyncEngine(tmp_registry)
        report = engine.sync(source_env_file, dry_run=True)

        assert report.results[0].applied is False
        assert Path(target_env_file).read_text() == original

    def test_no_changes_skips_project(self, tmp_registry, source_env_file):
        tmp_registry.register("same", source_env_file)
        engine = SyncEngine(tmp_registry)
        report = engine.sync(source_env_file, dry_run=False)
        assert report.results[0].applied is False
        assert not report.results[0].diff.has_changes

    def test_missing_target_creates_file(self, tmp_registry, source_env_file, tmp_path):
        new_path = str(tmp_path / "new_project" / ".env")
        Path(new_path).parent.mkdir(parents=True)
        tmp_registry.register("new_project", new_path)
        engine = SyncEngine(tmp_registry)
        report = engine.sync(source_env_file, dry_run=False)
        assert report.results[0].applied is True
        assert Path(new_path).exists()

    def test_error_captured_in_result(self, tmp_registry, source_env_file):
        tmp_registry.register("bad", "/nonexistent/dir/that/cant/be/created/.env")
        engine = SyncEngine(tmp_registry)
        report = engine.sync(source_env_file, dry_run=False)
        assert report.results[0].error is not None
        assert report.failed == 1
