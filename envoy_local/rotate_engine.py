"""Engine for rotating (regenerating) secret values in .env files."""

from __future__ import annotations

import secrets
import string
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

from envoy_local.env_file import EnvFile
from envoy_local.secret_mask import SecretMasker


_DEFAULT_ALPHABET = string.ascii_letters + string.digits + "!@#$%^&*"
_DEFAULT_LENGTH = 32


def _default_generator(length: int = _DEFAULT_LENGTH) -> str:
    """Generate a cryptographically secure random secret."""
    return "".join(secrets.choice(_DEFAULT_ALPHABET) for _ in range(length))


@dataclass
class RotateResult:
    rotated: List[str] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)
    errors: Dict[str, str] = field(default_factory=dict)

    @property
    def success(self) -> bool:
        return not self.errors

    def summary(self) -> str:
        parts = [f"Rotated: {len(self.rotated)}"]
        if self.skipped:
            parts.append(f"Skipped: {len(self.skipped)}")
        if self.errors:
            parts.append(f"Errors: {len(self.errors)}")
        return " | ".join(parts)

    def __repr__(self) -> str:
        return f"<RotateResult rotated={self.rotated} skipped={self.skipped} errors={self.errors}>"


class RotateEngine:
    """Rotates secret values in an EnvFile, optionally filtering by key."""

    def __init__(
        self,
        generator: Optional[Callable[[], str]] = None,
        masker: Optional[SecretMasker] = None,
    ) -> None:
        self._generator = generator or _default_generator
        self._masker = masker or SecretMasker()

    def rotate(
        self,
        env_file: EnvFile,
        keys: Optional[List[str]] = None,
        only_secrets: bool = True,
        dry_run: bool = False,
    ) -> RotateResult:
        """Rotate values for the given keys (or all secret keys if none specified)."""
        result = RotateResult()
        all_keys = list(env_file.keys())
        target_keys = keys if keys is not None else all_keys

        for key in target_keys:
            if key not in all_keys:
                result.errors[key] = "Key not found in env file"
                continue
            if only_secrets and not self._masker.is_secret(key):
                result.skipped.append(key)
                continue
            try:
                new_value = self._generator()
                if not dry_run:
                    env_file.set(key, new_value)
                result.rotated.append(key)
            except Exception as exc:  # pragma: no cover
                result.errors[key] = str(exc)

        return result
