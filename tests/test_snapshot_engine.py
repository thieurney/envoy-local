"""Tests for SnapshotEngine and Snapshot dataclass."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from envoy_local.env_file import EnvFile
from envoy_local.snapshot_engine import Snapshot, SnapshotEngine


@pytest.fixture
def storage_path(tmp_path: Path) -> Path:
    return tmp_path / "snapshots.json"


@pytest.fixture
def env_file(tmp_path: Path) -> EnvFile:
    p = tmp_path / ".env"
    p.write_text("DB_HOST=localhost\nDB_PORT=5432\nSECRET_KEY=abc123\n")
    ef = EnvFile(p)
    ef.load()
    return ef


@pytest.fixture
def engine(storage_path: Path) -> SnapshotEngine:
    return SnapshotEngine(storage_path=storage_path)


class TestSnapshot:
    def test_to_dict_contains_required_keys(self):
        s = Snapshot(project="myapp", timestamp="2024-01-01T00:00:00+00:00", variables={"A": "1"})
        d = s.to_dict()
        assert "project" in d
        assert "timestamp" in d
        assert "variables" in d
        assert "label" in d

    def test_from_dict_roundtrip(self):
        original = Snapshot(
            project="myapp",
            timestamp="2024-01-01T00:00:00+00:00",
            variables={"KEY": "val"},
            label="before-deploy",
        )
        restored = Snapshot.from_dict(original.to_dict())
        assert restored.project == original.project
        assert restored.variables == original.variables
        assert restored.label == original.label

    def test_repr_contains_project_and_timestamp(self):
        s = Snapshot(project="proj", timestamp="2024-01-01T00:00:00+00:00", variables={})
        r = repr(s)
        assert "proj" in r
        assert "2024-01-01" in r


class TestSnapshotEngine:
    def test_capture_creates_snapshot(self, engine: SnapshotEngine, env_file: EnvFile):
        snap = engine.capture("myapp", env_file)
        assert snap.project == "myapp"
        assert snap.variables["DB_HOST"] == "localhost"

    def test_capture_persists_to_disk(self, storage_path: Path, env_file: EnvFile):
        engine = SnapshotEngine(storage_path=storage_path)
        engine.capture("myapp", env_file, label="v1")
        data = json.loads(storage_path.read_text())
        assert len(data) == 1
        assert data[0]["label"] == "v1"

    def test_list_returns_all_snapshots(self, engine: SnapshotEngine, env_file: EnvFile):
        engine.capture("alpha", env_file)
        engine.capture("beta", env_file)
        assert len(engine.list_snapshots()) == 2

    def test_list_filters_by_project(self, engine: SnapshotEngine, env_file: EnvFile):
        engine.capture("alpha", env_file)
        engine.capture("beta", env_file)
        result = engine.list_snapshots(project="alpha")
        assert len(result) == 1
        assert result[0].project == "alpha"

    def test_restore_writes_variables(self, engine: SnapshotEngine, env_file: EnvFile, tmp_path: Path):
        snap = engine.capture("myapp", env_file)
        target_path = tmp_path / ".env.restored"
        target_path.write_text("")
        target = EnvFile(target_path)
        target.load()
        engine.restore(snap, target)
        target2 = EnvFile(target_path)
        target2.load()
        assert target2.get("DB_HOST") == "localhost"

    def test_delete_removes_snapshot(self, engine: SnapshotEngine, env_file: EnvFile):
        snap = engine.capture("myapp", env_file)
        removed = engine.delete("myapp", snap.timestamp)
        assert removed is True
        assert len(engine.list_snapshots(project="myapp")) == 0

    def test_delete_nonexistent_returns_false(self, engine: SnapshotEngine):
        result = engine.delete("ghost", "2000-01-01T00:00:00+00:00")
        assert result is False

    def test_engine_reloads_from_disk(self, storage_path: Path, env_file: EnvFile):
        e1 = SnapshotEngine(storage_path=storage_path)
        e1.capture("myapp", env_file, label="reload-test")
        e2 = SnapshotEngine(storage_path=storage_path)
        snaps = e2.list_snapshots(project="myapp")
        assert len(snaps) == 1
        assert snaps[0].label == "reload-test"
