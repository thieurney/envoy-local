"""Pin engine: lock specific env keys to fixed values, preventing accidental overwrite."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envoy_local.env_file import EnvFile


@dataclass
class PinResult:
    pinned: List[str] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)
    error: Optional[str] = None

    @property
    def success(self) -> bool:
        return self.error is None

    def summary(self) -> str:
        if not self.success:
            return f"Pin failed: {self.error}"
        parts = []
        if self.pinned:
            parts.append(f"{len(self.pinned)} key(s) pinned")
        if self.skipped:
            parts.append(f"{len(self.skipped)} key(s) skipped (not found)")
        return ", ".join(parts) if parts else "Nothing to pin."

    def __repr__(self) -> str:
        return f"PinResult(pinned={self.pinned}, skipped={self.skipped}, success={self.success})"


PIN_COMMENT_MARKER = "# pinned"


class PinEngine:
    """Marks keys in an EnvFile as pinned by appending an inline comment marker."""

    def __init__(self, env_file: EnvFile) -> None:
        self._env = env_file

    def pin(self, keys: List[str]) -> PinResult:
        """Pin the given keys. Saves the file in place."""
        pinned: List[str] = []
        skipped: List[str] = []

        try:
            for key in keys:
                value = self._env.get(key)
                if value is None:
                    skipped.append(key)
                    continue
                # Store value with marker appended to raw line via set
                self._env.set(key, value, comment=PIN_COMMENT_MARKER)
                pinned.append(key)
            if pinned:
                self._env.save()
        except Exception as exc:  # noqa: BLE001
            return PinResult(pinned=pinned, skipped=skipped, error=str(exc))

        return PinResult(pinned=pinned, skipped=skipped)

    def list_pinned(self) -> List[str]:
        """Return keys that carry the pin marker."""
        return [
            key
            for key, meta in self._env.metadata().items()
            if PIN_COMMENT_MARKER in meta.get("comment", "")
        ]

    def unpin(self, keys: List[str]) -> PinResult:
        """Remove the pin marker from the given keys."""
        pinned: List[str] = []
        skipped: List[str] = []

        try:
            for key in keys:
                value = self._env.get(key)
                if value is None:
                    skipped.append(key)
                    continue
                self._env.set(key, value, comment="")
                pinned.append(key)
            if pinned:
                self._env.save()
        except Exception as exc:  # noqa: BLE001
            return PinResult(pinned=pinned, skipped=skipped, error=str(exc))

        return PinResult(pinned=pinned, skipped=skipped)
