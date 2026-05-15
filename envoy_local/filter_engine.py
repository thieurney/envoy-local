from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Callable
import re

from envoy_local.env_file import EnvFile


@dataclass
class FilterResult:
    matched: dict
    excluded: dict
    error: Optional[str] = None

    @property
    def success(self) -> bool:
        return self.error is None

    def summary(self) -> str:
        if not self.success:
            return f"Filter failed: {self.error}"
        return (
            f"Matched {len(self.matched)} key(s), "
            f"excluded {len(self.excluded)} key(s)."
        )

    def __repr__(self) -> str:
        return (
            f"FilterResult(matched={len(self.matched)}, "
            f"excluded={len(self.excluded)}, success={self.success})"
        )


class FilterEngine:
    """Filter keys in an EnvFile by pattern, prefix, or custom predicate."""

    def __init__(self, env_file: EnvFile) -> None:
        self._env = env_file

    def by_pattern(self, pattern: str, invert: bool = False) -> FilterResult:
        """Keep keys whose names match *pattern* (regex)."""
        try:
            rx = re.compile(pattern)
        except re.error as exc:
            return FilterResult(matched={}, excluded={}, error=str(exc))
        return self._apply(lambda k, _v: bool(rx.search(k)), invert=invert)

    def by_prefix(self, prefix: str, invert: bool = False) -> FilterResult:
        """Keep keys that start with *prefix* (case-sensitive)."""
        return self._apply(lambda k, _v: k.startswith(prefix), invert=invert)

    def by_predicate(
        self,
        predicate: Callable[[str, str], bool],
        invert: bool = False,
    ) -> FilterResult:
        """Keep keys for which *predicate(key, value)* returns True."""
        try:
            return self._apply(predicate, invert=invert)
        except Exception as exc:  # noqa: BLE001
            return FilterResult(matched={}, excluded={}, error=str(exc))

    # ------------------------------------------------------------------
    def _apply(
        self,
        predicate: Callable[[str, str], bool],
        *,
        invert: bool,
    ) -> FilterResult:
        matched: dict = {}
        excluded: dict = {}
        all_keys = self._env.keys()
        for key in all_keys:
            value = self._env.get(key, "")
            hit = predicate(key, value)
            if hit ^ invert:
                matched[key] = value
            else:
                excluded[key] = value
        return FilterResult(matched=matched, excluded=excluded)
