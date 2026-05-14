"""Engine for promoting env values from one environment tier to another."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from envoy_local.env_file import EnvFile


@dataclass
class PromoteResult:
    promoted: Dict[str, str] = field(default_factory=dict)
    skipped: List[str] = field(default_factory=list)
    overwritten: List[str] = field(default_factory=list)
    error: Optional[str] = None

    @property
    def success(self) -> bool:
        return self.error is None

    def summary(self) -> str:
        if not self.success:
            return f"Promote failed: {self.error}"
        parts = [f"{len(self.promoted)} key(s) promoted"]
        if self.overwritten:
            parts.append(f"{len(self.overwritten)} overwritten")
        if self.skipped:
            parts.append(f"{len(self.skipped)} skipped")
        return ", ".join(parts)

    def __repr__(self) -> str:
        return (
            f"PromoteResult(promoted={len(self.promoted)}, "
            f"skipped={len(self.skipped)}, success={self.success})"
        )


class PromoteEngine:
    def __init__(self, keys: Optional[List[str]] = None, overwrite: bool = False):
        """
        Args:
            keys: Specific keys to promote. If None, all keys are promoted.
            overwrite: Whether to overwrite existing keys in the target.
        """
        self.keys = keys
        self.overwrite = overwrite

    def promote(
        self, source: EnvFile, target: EnvFile, dry_run: bool = False
    ) -> PromoteResult:
        """Promote keys from source env into target env."""
        result = PromoteResult()

        source_data = source.all()
        target_data = target.all()

        keys_to_promote = self.keys if self.keys is not None else list(source_data.keys())

        for key in keys_to_promote:
            if key not in source_data:
                result.skipped.append(key)
                continue

            value = source_data[key]

            if key in target_data and not self.overwrite:
                result.skipped.append(key)
                continue

            if key in target_data:
                result.overwritten.append(key)

            result.promoted[key] = value

        if not dry_run and result.success:
            for key, value in result.promoted.items():
                target.set(key, value)
            target.save()

        return result
