"""Engine for detecting and removing duplicate keys in .env files."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from envoy_local.env_file import EnvFile


@dataclass
class DedupeResult:
    duplicates: List[str] = field(default_factory=list)
    removed: List[str] = field(default_factory=list)
    error: Optional[str] = None

    @property
    def success(self) -> bool:
        return self.error is None

    @property
    def summary(self) -> str:
        if not self.success:
            return f"Dedupe failed: {self.error}"
        if not self.duplicates:
            return "No duplicate keys found."
        removed_count = len(self.removed)
        dup_count = len(self.duplicates)
        return (
            f"Found {dup_count} duplicate key(s); "
            f"removed {removed_count} redundant occurrence(s)."
        )

    def __repr__(self) -> str:
        return (
            f"DedupeResult(success={self.success}, "
            f"duplicates={self.duplicates}, removed={self.removed})"
        )


class DedupeEngine:
    """Detects and optionally removes duplicate keys from an EnvFile."""

    def __init__(self, env_file: EnvFile) -> None:
        self._env = env_file

    def find_duplicates(self) -> List[str]:
        """Return a list of keys that appear more than once in the raw file."""
        seen: dict[str, int] = {}
        for key in self._env.keys():
            seen[key] = seen.get(key, 0) + 1
        return [k for k, count in seen.items() if count > 1]

    def dedupe(self, dry_run: bool = False) -> DedupeResult:
        """Remove duplicate keys, keeping the last occurrence.

        Args:
            dry_run: If True, report duplicates without modifying the file.

        Returns:
            DedupeResult describing what was (or would be) changed.
        """
        try:
            duplicates = self.find_duplicates()
            if not duplicates or dry_run:
                return DedupeResult(duplicates=duplicates)

            removed: List[str] = []
            seen: set[str] = set()
            # Walk keys in reverse to keep the *last* occurrence
            all_keys = list(self._env.keys())
            keys_to_keep: set[str] = set()
            for key in reversed(all_keys):
                if key not in keys_to_keep:
                    keys_to_keep.add(key)
                else:
                    removed.append(key)

            # Rebuild env keeping only the last occurrence of each key
            new_data: dict[str, str] = {}
            for key in all_keys:
                if key not in seen:
                    new_data[key] = self._env.get(key, "")
                    seen.add(key)
                # Overwrite with the later value (last wins)
                new_data[key] = self._env.get(key, "")

            self._env._data = new_data  # type: ignore[attr-defined]
            self._env.save()
            return DedupeResult(duplicates=duplicates, removed=removed)
        except Exception as exc:  # pragma: no cover
            return DedupeResult(error=str(exc))
