"""Merge engine for combining .env files with conflict resolution strategies."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional

from envoy_local.env_file import EnvFile


class MergeStrategy(Enum):
    BASE_WINS = "base_wins"
    TARGET_WINS = "target_wins"
    UNION = "union"


@dataclass
class MergeConflict:
    key: str
    base_value: str
    target_value: str
    resolved_value: str

    def __repr__(self) -> str:
        return f"<MergeConflict key={self.key!r} base={self.base_value!r} target={self.target_value!r}>"


@dataclass
class MergeResult:
    merged: Dict[str, str] = field(default_factory=dict)
    conflicts: List[MergeConflict] = field(default_factory=list)
    added_keys: List[str] = field(default_factory=list)
    strategy: MergeStrategy = MergeStrategy.BASE_WINS

    @property
    def has_conflicts(self) -> bool:
        return len(self.conflicts) > 0

    def summary(self) -> str:
        parts = [f"Merged {len(self.merged)} keys"]
        if self.added_keys:
            parts.append(f"{len(self.added_keys)} added from target")
        if self.conflicts:
            parts.append(f"{len(self.conflicts)} conflicts resolved via {self.strategy.value}")
        return ", ".join(parts) + "."


class MergeEngine:
    def __init__(self, strategy: MergeStrategy = MergeStrategy.BASE_WINS):
        self.strategy = strategy

    def merge(self, base: EnvFile, target: EnvFile) -> MergeResult:
        result = MergeResult(strategy=self.strategy)
        base_data = base.all()
        target_data = target.all()

        result.merged.update(base_data)

        for key, target_val in target_data.items():
            if key not in base_data:
                result.merged[key] = target_val
                result.added_keys.append(key)
            elif base_data[key] != target_val:
                base_val = base_data[key]
                if self.strategy == MergeStrategy.TARGET_WINS:
                    resolved = target_val
                else:
                    resolved = base_val
                result.merged[key] = resolved
                result.conflicts.append(
                    MergeConflict(
                        key=key,
                        base_value=base_val,
                        target_value=target_val,
                        resolved_value=resolved,
                    )
                )

        return result
