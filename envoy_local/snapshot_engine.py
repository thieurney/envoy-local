"""Snapshot engine for capturing and restoring .env file states."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from envoy_local.env_file import EnvFile


@dataclass
class Snapshot:
    project: str
    timestamp: str
    variables: Dict[str, str]
    label: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "project": self.project,
            "timestamp": self.timestamp,
            "variables": self.variables,
            "label": self.label,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Snapshot":
        return cls(
            project=data["project"],
            timestamp=data["timestamp"],
            variables=data["variables"],
            label=data.get("label"),
        )

    def __repr__(self) -> str:
        label_part = f" ({self.label})" if self.label else ""
        return f"<Snapshot project={self.project!r} at={self.timestamp}{label_part}>"


class SnapshotEngine:
    def __init__(self, storage_path: Path) -> None:
        self.storage_path = storage_path
        self._snapshots: List[Snapshot] = []
        self._load()

    def _load(self) -> None:
        if self.storage_path.exists():
            raw = json.loads(self.storage_path.read_text(encoding="utf-8"))
            self._snapshots = [Snapshot.from_dict(s) for s in raw]
        else:
            self._snapshots = []

    def _save(self) -> None:
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.storage_path.write_text(
            json.dumps([s.to_dict() for s in self._snapshots], indent=2),
            encoding="utf-8",
        )

    def capture(self, project: str, env_file: EnvFile, label: Optional[str] = None) -> Snapshot:
        timestamp = datetime.now(timezone.utc).isoformat()
        snapshot = Snapshot(
            project=project,
            timestamp=timestamp,
            variables=dict(env_file.all()),
            label=label,
        )
        self._snapshots.append(snapshot)
        self._save()
        return snapshot

    def list_snapshots(self, project: Optional[str] = None) -> List[Snapshot]:
        if project is None:
            return list(self._snapshots)
        return [s for s in self._snapshots if s.project == project]

    def restore(self, snapshot: Snapshot, target: EnvFile) -> None:
        for key, value in snapshot.variables.items():
            target.set(key, value)
        target.save()

    def delete(self, project: str, timestamp: str) -> bool:
        before = len(self._snapshots)
        self._snapshots = [
            s for s in self._snapshots
            if not (s.project == project and s.timestamp == timestamp)
        ]
        if len(self._snapshots) < before:
            self._save()
            return True
        return False
