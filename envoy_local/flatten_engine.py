"""Engine for flattening nested env var prefixes into a single-level structure."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envoy_local.env_file import EnvFile


@dataclass
class FlattenResult:
    flattened: Dict[str, str] = field(default_factory=dict)
    skipped: List[str] = field(default_factory=list)
    error: Optional[str] = None

    @property
    def success(self) -> bool:
        return self.error is None

    @property
    def summary(self) -> str:
        if not self.success:
            return f"Flatten failed: {self.error}"
        return (
            f"Flattened {len(self.flattened)} key(s), "
            f"skipped {len(self.skipped)} key(s)."
        )

    def __repr__(self) -> str:
        return (
            f"FlattenResult(success={self.success}, "
            f"flattened={len(self.flattened)}, "
            f"skipped={len(self.skipped)})"
        )


class FlattenEngine:
    """Flatten env vars by stripping a common prefix and normalising separators."""

    def __init__(self, separator: str = "__") -> None:
        self.separator = separator

    def flatten(
        self,
        env_file: EnvFile,
        prefix: Optional[str] = None,
        strip_prefix: bool = True,
        dry_run: bool = False,
    ) -> FlattenResult:
        """Flatten keys in *env_file* that match *prefix*.

        Args:
            env_file:     Source EnvFile to process.
            prefix:       Only process keys that start with this prefix.
                          If *None*, all keys are processed.
            strip_prefix: When *True* (default) the prefix is removed from
                          the resulting key name.
            dry_run:      When *True* the file is not written back to disk.
        """
        try:
            data = env_file.all()
        except Exception as exc:  # pragma: no cover
            return FlattenResult(error=str(exc))

        flattened: Dict[str, str] = {}
        skipped: List[str] = []

        for key, value in data.items():
            normalised = key.replace(self.separator, "_")
            if prefix:
                upper_prefix = prefix.upper().rstrip("_") + "_"
                if not key.upper().startswith(upper_prefix):
                    skipped.append(key)
                    continue
                if strip_prefix:
                    normalised = normalised[len(upper_prefix):]
            flattened[normalised] = value

        if not dry_run and flattened:
            for old_key in list(data.keys()):
                if old_key not in skipped:
                    env_file.unset(old_key)
            for new_key, value in flattened.items():
                env_file.set(new_key, value)
            env_file.save()

        return FlattenResult(flattened=flattened, skipped=skipped)
