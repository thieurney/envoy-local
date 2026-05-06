"""Diff engine for comparing .env files across projects or versions."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from envoy_local.env_file import EnvFile
from envoy_local.secret_mask import SecretMasker


@dataclass
class DiffResult:
    """Holds the result of comparing two env files."""

    added: Dict[str, str] = field(default_factory=dict)
    removed: Dict[str, str] = field(default_factory=dict)
    changed: Dict[str, Tuple[str, str]] = field(default_factory=dict)  # key -> (old, new)
    unchanged: List[str] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return bool(self.added or self.removed or self.changed)

    def summary(self) -> str:
        lines = []
        lines.append(f"Added:     {len(self.added)}")
        lines.append(f"Removed:   {len(self.removed)}")
        lines.append(f"Changed:   {len(self.changed)}")
        lines.append(f"Unchanged: {len(self.unchanged)}")
        return "\n".join(lines)


class DiffEngine:
    """Compares two EnvFile instances and reports differences."""

    def __init__(self, mask_secrets: bool = True):
        self.mask_secrets = mask_secrets
        self._masker = SecretMasker() if mask_secrets else None

    def compare(self, base: EnvFile, target: EnvFile) -> DiffResult:
        """Compare base env file against target and return a DiffResult."""
        base_data = base.all()
        target_data = target.all()

        base_keys = set(base_data.keys())
        target_keys = set(target_data.keys())

        result = DiffResult()

        for key in target_keys - base_keys:
            value = target_data[key]
            result.added[key] = self._maybe_mask(key, value)

        for key in base_keys - target_keys:
            value = base_data[key]
            result.removed[key] = self._maybe_mask(key, value)

        for key in base_keys & target_keys:
            old_val = base_data[key]
            new_val = target_data[key]
            if old_val != new_val:
                result.changed[key] = (
                    self._maybe_mask(key, old_val),
                    self._maybe_mask(key, new_val),
                )
            else:
                result.unchanged.append(key)

        return result

    def _maybe_mask(self, key: str, value: str) -> str:
        if self._masker and self._masker.is_secret(key):
            return self._masker.mask(value)
        return value

    def format_diff(self, result: DiffResult) -> str:
        """Return a human-readable diff string."""
        lines = []
        for key, value in sorted(result.added.items()):
            lines.append(f"+ {key}={value}")
        for key, value in sorted(result.removed.items()):
            lines.append(f"- {key}={value}")
        for key, (old, new) in sorted(result.changed.items()):
            lines.append(f"~ {key}: {old!r} -> {new!r}")
        return "\n".join(lines) if lines else "(no changes)"
