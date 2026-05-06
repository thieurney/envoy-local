"""Utilities for masking secret values when displaying .env contents."""

from __future__ import annotations

import re
from typing import Dict, FrozenSet

DEFAULT_SECRET_PATTERNS: FrozenSet[str] = frozenset({
    r'.*SECRET.*',
    r'.*PASSWORD.*',
    r'.*PASSWD.*',
    r'.*TOKEN.*',
    r'.*API_KEY.*',
    r'.*PRIVATE_KEY.*',
    r'.*AUTH.*',
    r'.*CREDENTIAL.*',
})

MASK_PLACEHOLDER = "********"


class SecretMasker:
    """Masks sensitive environment variable values based on key name patterns."""

    def __init__(
        self,
        patterns: FrozenSet[str] | None = None,
        reveal_chars: int = 0,
    ) -> None:
        self._patterns = patterns if patterns is not None else DEFAULT_SECRET_PATTERNS
        self._reveal_chars = reveal_chars
        self._compiled = [
            re.compile(p, re.IGNORECASE) for p in self._patterns
        ]

    def is_secret(self, key: str) -> bool:
        """Return True if the key matches any secret pattern."""
        return any(pattern.fullmatch(key) for pattern in self._compiled)

    def mask(self, key: str, value: str) -> str:
        """Return masked value if key is a secret, otherwise return value as-is."""
        if not self.is_secret(key):
            return value
        if self._reveal_chars > 0 and len(value) > self._reveal_chars:
            visible = value[: self._reveal_chars]
            return f"{visible}{MASK_PLACEHOLDER}"
        return MASK_PLACEHOLDER

    def mask_dict(
        self, entries: Dict[str, str]
    ) -> Dict[str, str]:
        """Return a new dict with secret values masked."""
        return {key: self.mask(key, value) for key, value in entries.items()}

    def add_pattern(self, pattern: str) -> None:
        """Register an additional secret key pattern at runtime."""
        self._patterns = self._patterns | frozenset({pattern})
        self._compiled.append(re.compile(pattern, re.IGNORECASE))
