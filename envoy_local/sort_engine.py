"""Engine for sorting keys in .env files alphabetically or by custom order."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional

from envoy_local.env_file import EnvFile


class SortOrder(str, Enum):
    ALPHA_ASC = "asc"
    ALPHA_DESC = "desc"
    LENGTH_ASC = "length_asc"
    LENGTH_DESC = "length_desc"


@dataclass
class SortResult:
    original_order: List[str]
    sorted_order: List[str]
    error: Optional[str] = None
    saved: bool = False

    @property
    def success(self) -> bool:
        return self.error is None

    @property
    def changed(self) -> bool:
        return self.original_order != self.sorted_order

    def summary(self) -> str:
        if not self.success:
            return f"Sort failed: {self.error}"
        if not self.changed:
            return "Keys already in desired order — no changes made."
        status = "saved" if self.saved else "dry-run"
        return (
            f"Sorted {len(self.sorted_order)} keys ({status}). "
            f"Order changed: {self.original_order[:3]}... → {self.sorted_order[:3]}..."
        )

    def __repr__(self) -> str:
        return (
            f"SortResult(success={self.success}, changed={self.changed}, "
            f"keys={len(self.sorted_order)}, saved={self.saved})"
        )


class SortEngine:
    def __init__(self, env_file: EnvFile) -> None:
        self._env = env_file

    def sort(
        self,
        order: SortOrder = SortOrder.ALPHA_ASC,
        dry_run: bool = True,
    ) -> SortResult:
        original_keys = list(self._env.keys())

        try:
            sorted_keys = self._sort_keys(original_keys, order)
        except Exception as exc:  # pragma: no cover
            return SortResult(
                original_order=original_keys,
                sorted_order=original_keys,
                error=str(exc),
            )

        result = SortResult(
            original_order=original_keys,
            sorted_order=sorted_keys,
        )

        if result.changed and not dry_run:
            sorted_data = {k: self._env.get(k, "") for k in sorted_keys}
            self._env._data = sorted_data  # type: ignore[attr-defined]
            self._env.save()
            result.saved = True

        return result

    def _sort_keys(self, keys: List[str], order: SortOrder) -> List[str]:
        if order == SortOrder.ALPHA_ASC:
            return sorted(keys)
        if order == SortOrder.ALPHA_DESC:
            return sorted(keys, reverse=True)
        if order == SortOrder.LENGTH_ASC:
            return sorted(keys, key=len)
        if order == SortOrder.LENGTH_DESC:
            return sorted(keys, key=len, reverse=True)
        return keys  # pragma: no cover
