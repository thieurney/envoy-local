"""Core module for reading, writing, and managing .env files."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Dict, Optional, Tuple

ENV_LINE_PATTERN = re.compile(
    r'^(?P<key>[A-Za-z_][A-Za-z0-9_]*)\s*=\s*(?P<value>.*)$'
)
COMMENT_PATTERN = re.compile(r'^\s*#.*$')


class EnvFile:
    """Represents a single .env file with parsed key-value pairs."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._entries: Dict[str, str] = {}
        self._raw_lines: list[str] = []

    def load(self) -> "EnvFile":
        """Load and parse the .env file from disk."""
        if not self.path.exists():
            raise FileNotFoundError(f".env file not found: {self.path}")

        self._raw_lines = self.path.read_text(encoding="utf-8").splitlines()
        self._entries = {}

        for line in self._raw_lines:
            match = ENV_LINE_PATTERN.match(line.strip())
            if match:
                key = match.group("key")
                value = _strip_quotes(match.group("value").strip())
                self._entries[key] = value

        return self

    def save(self) -> None:
        """Persist current entries back to disk, preserving comments and order."""
        updated_keys: set[str] = set()
        new_lines: list[str] = []

        for line in self._raw_lines:
            match = ENV_LINE_PATTERN.match(line.strip())
            if match:
                key = match.group("key")
                if key in self._entries:
                    new_lines.append(f"{key}={self._entries[key]}")
                    updated_keys.add(key)
                else:
                    new_lines.append(line)
            else:
                new_lines.append(line)

        for key, value in self._entries.items():
            if key not in updated_keys:
                new_lines.append(f"{key}={value}")

        self.path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")

    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        return self._entries.get(key, default)

    def set(self, key: str, value: str) -> None:
        self._entries[key] = value

    def delete(self, key: str) -> bool:
        if key in self._entries:
            del self._entries[key]
            self._raw_lines = [
                line for line in self._raw_lines
                if not ENV_LINE_PATTERN.match(line.strip()) or
                ENV_LINE_PATTERN.match(line.strip()).group("key") != key  # type: ignore[union-attr]
            ]
            return True
        return False

    @property
    def entries(self) -> Dict[str, str]:
        return dict(self._entries)

    def __repr__(self) -> str:
        return f"EnvFile(path={self.path!r}, keys={list(self._entries.keys())})"


def _strip_quotes(value: str) -> str:
    """Remove surrounding single or double quotes from a value."""
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
        return value[1:-1]
    return value
