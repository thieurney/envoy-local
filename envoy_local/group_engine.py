"""Group engine: assign keys in an env file to named groups and filter by group."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envoy_local.env_file import EnvFile


@dataclass
class GroupResult:
    group_name: str
    keys: List[str] = field(default_factory=list)
    missing_keys: List[str] = field(default_factory=list)
    error: Optional[str] = None

    @property
    def success(self) -> bool:
        return self.error is None

    @property
    def summary(self) -> str:
        if not self.success:
            return f"Group '{self.group_name}' failed: {self.error}"
        parts = [f"Group '{self.group_name}': {len(self.keys)} key(s) assigned"]
        if self.missing_keys:
            parts.append(f"{len(self.missing_keys)} missing: {', '.join(self.missing_keys)}")
        return "; ".join(parts)

    def __repr__(self) -> str:
        return f"<GroupResult group={self.group_name!r} keys={len(self.keys)} success={self.success}>"


class GroupEngine:
    """Assign env keys to named groups and retrieve group subsets."""

    # Groups are stored as metadata in a sidecar dict, not in the env file itself.
    def __init__(self, env_file: EnvFile) -> None:
        self._env = env_file
        # group_name -> list of key names
        self._groups: Dict[str, List[str]] = {}

    def define_group(self, group_name: str, keys: List[str]) -> GroupResult:
        """Define (or overwrite) a group with the given key names."""
        if not group_name:
            return GroupResult(group_name=group_name, error="Group name must not be empty")
        if not keys:
            return GroupResult(group_name=group_name, error="Key list must not be empty")

        all_keys = self._env.keys()
        missing = [k for k in keys if k not in all_keys]
        self._groups[group_name] = list(keys)
        return GroupResult(group_name=group_name, keys=list(keys), missing_keys=missing)

    def get_group(self, group_name: str) -> GroupResult:
        """Return the keys (and their presence) for a named group."""
        if group_name not in self._groups:
            return GroupResult(group_name=group_name, error=f"Group '{group_name}' not found")
        keys = self._groups[group_name]
        all_keys = self._env.keys()
        missing = [k for k in keys if k not in all_keys]
        present = [k for k in keys if k in all_keys]
        return GroupResult(group_name=group_name, keys=present, missing_keys=missing)

    def list_groups(self) -> List[str]:
        """Return all defined group names."""
        return list(self._groups.keys())

    def filter_env(self, group_name: str) -> Optional[Dict[str, str]]:
        """Return a dict of key/value pairs for keys belonging to *group_name*."""
        if group_name not in self._groups:
            return None
        return {k: self._env.get(k) for k in self._groups[group_name] if self._env.get(k) is not None}

    def remove_group(self, group_name: str) -> bool:
        """Delete a group definition. Returns True if it existed."""
        if group_name in self._groups:
            del self._groups[group_name]
            return True
        return False
