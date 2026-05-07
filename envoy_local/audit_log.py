"""Audit log for tracking changes to .env files across projects."""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional


AUDIT_LOG_VERSION = 1


class AuditEntry:
    def __init__(self, action: str, project: str, key: str, detail: str = "", timestamp: Optional[str] = None):
        self.action = action
        self.project = project
        self.key = key
        self.detail = detail
        self.timestamp = timestamp or datetime.utcnow().isoformat()

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "action": self.action,
            "project": self.project,
            "key": self.key,
            "detail": self.detail,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AuditEntry":
        return cls(
            action=data["action"],
            project=data["project"],
            key=data["key"],
            detail=data.get("detail", ""),
            timestamp=data.get("timestamp"),
        )

    def __repr__(self) -> str:
        return f"[{self.timestamp}] {self.action} | {self.project} | {self.key} | {self.detail}"


class AuditLog:
    def __init__(self, log_path: str):
        self.log_path = Path(log_path)
        self._entries: List[AuditEntry] = []
        self._load()

    def _load(self):
        if self.log_path.exists():
            with open(self.log_path, "r") as f:
                data = json.load(f)
            self._entries = [AuditEntry.from_dict(e) for e in data.get("entries", [])]
        else:
            self._entries = []

    def _save(self):
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.log_path, "w") as f:
            json.dump({"version": AUDIT_LOG_VERSION, "entries": [e.to_dict() for e in self._entries]}, f, indent=2)

    def record(self, action: str, project: str, key: str, detail: str = ""):
        entry = AuditEntry(action=action, project=project, key=key, detail=detail)
        self._entries.append(entry)
        self._save()

    def entries(self, project: Optional[str] = None) -> List[AuditEntry]:
        if project:
            return [e for e in self._entries if e.project == project]
        return list(self._entries)

    def clear(self, project: Optional[str] = None):
        if project:
            self._entries = [e for e in self._entries if e.project != project]
        else:
            self._entries = []
        self._save()
