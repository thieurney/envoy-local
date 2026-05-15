"""Scope engine: filter env vars by prefix or pattern to create scoped subsets."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envoy_local.env_file import EnvFile


@dataclass
class ScopeResult:
    scoped: Dict[str, str] = field(default_factory=dict)
    excluded: List[str] = field(default_factory=list)
    error: Optional[str] = None

    @property
    def success(self) -> bool:
        return self.error is None

    def summary(self) -> str:
        if not self.success:
            return f"Scope failed: {self.error}"
        return (
            f"Scoped {len(self.scoped)} key(s), "
            f"excluded {len(self.excluded)} key(s)."
        )

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"ScopeResult(scoped={len(self.scoped)}, "
            f"excluded={len(self.excluded)}, success={self.success})"
        )


class ScopeEngine:
    """Filter an EnvFile's keys by prefix or regex pattern."""

    def __init__(self, env_file: EnvFile) -> None:
        self._env = env_file

    def by_prefix(
        self,
        prefix: str,
        strip_prefix: bool = False,
    ) -> ScopeResult:
        """Return keys that start with *prefix*.

        Args:
            prefix: The prefix string to match (case-sensitive).
            strip_prefix: If True, remove the prefix from the result keys.
        """
        if not prefix:
            return ScopeResult(error="Prefix must not be empty.")

        scoped: Dict[str, str] = {}
        excluded: List[str] = []

        for key, value in self._env.all().items():
            if key.startswith(prefix):
                result_key = key[len(prefix):] if strip_prefix else key
                scoped[result_key] = value
            else:
                excluded.append(key)

        return ScopeResult(scoped=scoped, excluded=excluded)

    def by_pattern(
        self,
        pattern: str,
    ) -> ScopeResult:
        """Return keys that match a regex *pattern*.

        Args:
            pattern: A regular-expression string matched against each key.
        """
        try:
            compiled = re.compile(pattern)
        except re.error as exc:
            return ScopeResult(error=f"Invalid regex pattern: {exc}")

        scoped: Dict[str, str] = {}
        excluded: List[str] = []

        for key, value in self._env.all().items():
            if compiled.search(key):
                scoped[key] = value
            else:
                excluded.append(key)

        return ScopeResult(scoped=scoped, excluded=excluded)
