"""Watch engine: monitors .env files for changes and emits events."""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Optional


@dataclass
class WatchEvent:
    path: str
    kind: str  # 'modified' | 'created' | 'deleted'
    timestamp: float = field(default_factory=time.time)

    def __repr__(self) -> str:
        return f"<WatchEvent kind={self.kind!r} path={self.path!r}>"


@dataclass
class WatchResult:
    events: List[WatchEvent] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return len(self.events) > 0

    def summary(self) -> str:
        if not self.events:
            return "No changes detected."
        lines = [f"{e.kind.upper()}: {e.path}" for e in self.events]
        return "\n".join(lines)


class WatchEngine:
    """Polls registered .env file paths and detects changes via content hash."""

    def __init__(self) -> None:
        self._hashes: Dict[str, Optional[str]] = {}
        self._callbacks: List[Callable[[WatchEvent], None]] = []

    def register(self, path: str) -> None:
        p = Path(path)
        self._hashes[path] = self._hash(p) if p.exists() else None

    def on_change(self, callback: Callable[[WatchEvent], None]) -> None:
        self._callbacks.append(callback)

    def poll(self) -> WatchResult:
        result = WatchResult()
        for path, old_hash in list(self._hashes.items()):
            p = Path(path)
            try:
                if p.exists():
                    new_hash = self._hash(p)
                    if old_hash is None:
                        event = WatchEvent(path=path, kind="created")
                    elif new_hash != old_hash:
                        event = WatchEvent(path=path, kind="modified")
                    else:
                        continue
                    self._hashes[path] = new_hash
                else:
                    if old_hash is not None:
                        event = WatchEvent(path=path, kind="deleted")
                        self._hashes[path] = None
                    else:
                        continue
                result.events.append(event)
                for cb in self._callbacks:
                    cb(event)
            except OSError as exc:
                result.errors.append(f"{path}: {exc}")
        return result

    @staticmethod
    def _hash(path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()
