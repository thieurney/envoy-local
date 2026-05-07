"""Clone engine: copy an env file to a new location, optionally filtering keys."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from envoy_local.env_file import EnvFile


@dataclass
class CloneResult:
    source: Path
    destination: Path
    copied_keys: List[str] = field(default_factory=list)
    skipped_keys: List[str] = field(default_factory=list)
    error: Optional[str] = None

    @property
    def success(self) -> bool:
        return self.error is None

    def summary(self) -> str:
        if not self.success:
            return f"Clone failed: {self.error}"
        return (
            f"Cloned {len(self.copied_keys)} key(s) from '{self.source}' "
            f"to '{self.destination}'"
            + (f", skipped {len(self.skipped_keys)} key(s)" if self.skipped_keys else "")
        )

    def __repr__(self) -> str:  # pragma: no cover
        return f"CloneResult(success={self.success}, copied={len(self.copied_keys)})"


class CloneEngine:
    """Copies an EnvFile to a new path, with optional key inclusion/exclusion filters."""

    def __init__(self, source: EnvFile) -> None:
        self.source = source

    def clone(
        self,
        destination: Path,
        include_keys: Optional[List[str]] = None,
        exclude_keys: Optional[List[str]] = None,
        overwrite: bool = False,
    ) -> CloneResult:
        result = CloneResult(source=self.source.path, destination=destination)

        if destination.exists() and not overwrite:
            result.error = f"Destination '{destination}' already exists. Use overwrite=True to replace."
            return result

        all_keys = list(self.source.all().keys())
        exclude_set = set(exclude_keys or [])
        include_set = set(include_keys) if include_keys is not None else None

        selected: dict = {}
        for key in all_keys:
            if key in exclude_set:
                result.skipped_keys.append(key)
                continue
            if include_set is not None and key not in include_set:
                result.skipped_keys.append(key)
                continue
            selected[key] = self.source.get(key)
            result.copied_keys.append(key)

        try:
            dest_env = EnvFile(destination)
            for k, v in selected.items():
                dest_env.set(k, v)
            dest_env.save()
        except Exception as exc:  # pragma: no cover
            result.error = str(exc)
            return result

        return result
