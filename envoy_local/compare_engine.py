"""Compare two .env files across projects and report value drift."""
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from envoy_local.env_file import EnvFile
from envoy_local.secret_mask import SecretMasker


@dataclass
class CompareEntry:
    key: str
    left_value: Optional[str]
    right_value: Optional[str]

    @property
    def is_same(self) -> bool:
        return self.left_value == self.right_value

    @property
    def status(self) -> str:
        if self.left_value is None:
            return "only_right"
        if self.right_value is None:
            return "only_left"
        if self.is_same:
            return "equal"
        return "differs"

    def __repr__(self) -> str:
        return f"CompareEntry(key={self.key!r}, status={self.status})"


@dataclass
class CompareResult:
    entries: List[CompareEntry] = field(default_factory=list)
    left_label: str = "left"
    right_label: str = "right"

    @property
    def has_differences(self) -> bool:
        return any(not e.is_same for e in self.entries)

    @property
    def differing_keys(self) -> List[str]:
        return [e.key for e in self.entries if not e.is_same]

    def summary(self) -> str:
        total = len(self.entries)
        diffs = len(self.differing_keys)
        return (
            f"Compared {total} keys between '{self.left_label}' and "
            f"'{self.right_label}': {diffs} difference(s) found."
        )


class CompareEngine:
    def __init__(self, mask_secrets: bool = False):
        self.mask_secrets = mask_secrets
        self._masker = SecretMasker()

    def compare(
        self,
        left: EnvFile,
        right: EnvFile,
        left_label: str = "left",
        right_label: str = "right",
    ) -> CompareResult:
        all_keys = sorted(set(left.keys()) | set(right.keys()))
        entries: List[CompareEntry] = []

        for key in all_keys:
            lv = left.get(key)
            rv = right.get(key)
            if self.mask_secrets:
                lv = self._masker.mask(key, lv) if lv is not None else None
                rv = self._masker.mask(key, rv) if rv is not None else None
            entries.append(CompareEntry(key=key, left_value=lv, right_value=rv))

        return CompareResult(
            entries=entries,
            left_label=left_label,
            right_label=right_label,
        )
