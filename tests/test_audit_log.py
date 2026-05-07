"""Tests for audit_log.py and cli_audit.py."""

import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from envoy_local.audit_log import AuditLog, AuditEntry


@pytest.fixture
def log(tmp_path):
    return AuditLog(log_path=str(tmp_path / "audit.json"))


class TestAuditEntry:
    def test_to_dict_contains_required_keys(self):
        entry = AuditEntry(action="set", project="myapp", key="DB_URL", detail="added")
        d = entry.to_dict()
        assert d["action"] == "set"
        assert d["project"] == "myapp"
        assert d["key"] == "DB_URL"
        assert "timestamp" in d

    def test_from_dict_roundtrip(self):
        entry = AuditEntry(action="delete", project="proj", key="SECRET", detail="removed")
        restored = AuditEntry.from_dict(entry.to_dict())
        assert restored.action == entry.action
        assert restored.project == entry.project
        assert restored.key == entry.key
        assert restored.timestamp == entry.timestamp

    def test_repr_contains_action_and_key(self):
        entry = AuditEntry(action="sync", project="p", key="K")
        assert "sync" in repr(entry)
        assert "K" in repr(entry)


class TestAuditLog:
    def test_empty_on_init(self, log):
        assert log.entries() == []

    def test_record_adds_entry(self, log):
        log.record("set", "myapp", "API_KEY", "new value")
        entries = log.entries()
        assert len(entries) == 1
        assert entries[0].action == "set"
        assert entries[0].key == "API_KEY"

    def test_record_persists_to_disk(self, tmp_path):
        path = str(tmp_path / "audit.json")
        log1 = AuditLog(log_path=path)
        log1.record("set", "proj", "FOO")
        log2 = AuditLog(log_path=path)
        assert len(log2.entries()) == 1

    def test_filter_by_project(self, log):
        log.record("set", "alpha", "X")
        log.record("set", "beta", "Y")
        assert len(log.entries(project="alpha")) == 1
        assert log.entries(project="alpha")[0].project == "alpha"

    def test_clear_all(self, log):
        log.record("set", "proj", "A")
        log.record("set", "proj", "B")
        log.clear()
        assert log.entries() == []

    def test_clear_by_project(self, log):
        log.record("set", "alpha", "A")
        log.record("set", "beta", "B")
        log.clear(project="alpha")
        remaining = log.entries()
        assert len(remaining) == 1
        assert remaining[0].project == "beta"

    def test_multiple_entries_ordered(self, log):
        for key in ["A", "B", "C"]:
            log.record("set", "proj", key)
        keys = [e.key for e in log.entries()]
        assert keys == ["A", "B", "C"]
