"""Engine for redacting specific keys from .env files."""

from dataclasses import dataclass, field
from typing import List, Optional
from envoy_local.env_file import EnvFile


@dataclass
class RedactResult:
    redacted_keys: List[str] = field(default_factory=list)
    skipped_keys: List[str] = field(default_factory=list)
    error: Optional[str] = None

    @property
    def success(self) -> bool:
        return self.error is None

    @property
    def summary(self) -> str:
        if not self.success:
            return f"Redact failed: {self.error}"
        parts = [f"Redacted {len(self.redacted_keys)} key(s)"]
        if self.skipped_keys:
            parts.append(f"skipped {len(self.skipped_keys)} missing key(s)")
        return ", ".join(parts) + "."

    def __repr__(self) -> str:
        return (
            f"RedactResult(redacted={self.redacted_keys}, "
            f"skipped={self.skipped_keys}, success={self.success})"
        )


REDACT_PLACEHOLDER = "***REDACTED***"


class RedactEngine:
    def __init__(self, placeholder: str = REDACT_PLACEHOLDER):
        self.placeholder = placeholder

    def redact(self, env_file: EnvFile, keys: List[str], save: bool = True) -> RedactResult:
        """Replace values of given keys with the placeholder."""
        result = RedactResult()
        try:
            for key in keys:
                current = env_file.get(key)
                if current is None:
                    result.skipped_keys.append(key)
                else:
                    env_file.set(key, self.placeholder)
                    result.redacted_keys.append(key)
            if save and result.redacted_keys:
                env_file.save()
        except Exception as exc:  # noqa: BLE001
            result.error = str(exc)
        return result

    def redact_pattern(self, env_file: EnvFile, pattern: str, save: bool = True) -> RedactResult:
        """Redact all keys whose names contain the given substring (case-insensitive)."""
        import re
        matching = [
            k for k in env_file.keys()
            if re.search(pattern, k, re.IGNORECASE)
        ]
        return self.redact(env_file, matching, save=save)
