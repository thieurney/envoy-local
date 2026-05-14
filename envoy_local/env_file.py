"""EnvFile: load, manipulate and save .env files with optional metadata support."""

from __future__ import annotations

import os
import re
from typing import Any, Dict, Iterator, List, Optional, Tuple

_LINE_RE = re.compile(
    r"^\s*(?P<key>[A-Za-z_][A-Za-z0-9_]*)\s*=\s*(?P<value>[^#]*)(?P<comment>#.*)?$"
)


class EnvFile:
    """Represents a single .env file on disk."""

    def __init__(self, path: str) -> None:
        self.path = path
        self._data: Dict[str, str] = {}
        self._meta: Dict[str, Dict[str, Any]] = {}
        self._order: List[str] = []

    # ------------------------------------------------------------------
    # I/O
    # ------------------------------------------------------------------

    def load(self) -> None:
        """Parse the file from disk."""
        self._data.clear()
        self._meta.clear()
        self._order.clear()

        if not os.path.exists(self.path):
            raise FileNotFoundError(f".env file not found: {self.path}")

        with open(self.path, encoding="utf-8") as fh:
            for line in fh:
                line = line.rstrip("\n")
                m = _LINE_RE.match(line)
                if not m:
                    continue
                key = m.group("key")
                raw_value = m.group("value").strip()
                comment = (m.group("comment") or "").strip()
                # Strip surrounding quotes
                if len(raw_value) >= 2 and raw_value[0] in ('"', "'") and raw_value[0] == raw_value[-1]:
                    raw_value = raw_value[1:-1]
                self._data[key] = raw_value
                self._meta[key] = {"comment": comment}
                if key not in self._order:
                    self._order.append(key)

    def save(self) -> None:
        """Write the current state back to disk."""
        lines: List[str] = []
        for key in self._order:
            value = self._data.get(key, "")
            comment = self._meta.get(key, {}).get("comment", "")
            line = f'{key}="{value}"'
            if comment:
                line = f"{line}  {comment}"
            lines.append(line)
        with open(self.path, "w", encoding="utf-8") as fh:
            fh.write("\n".join(lines) + ("\n" if lines else ""))

    # ------------------------------------------------------------------
    # Data access
    # ------------------------------------------------------------------

    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        return self._data.get(key, default)

    def set(self, key: str, value: str, comment: str = "") -> None:
        if key not in self._order:
            self._order.append(key)
        self._data[key] = value
        if key not in self._meta:
            self._meta[key] = {}
        self._meta[key]["comment"] = comment

    def delete(self, key: str) -> bool:
        if key in self._data:
            del self._data[key]
            del self._meta[key]
            self._order.remove(key)
            return True
        return False

    def keys(self) -> List[str]:
        return list(self._order)

    def items(self) -> Iterator[Tuple[str, str]]:
        for key in self._order:
            yield key, self._data[key]

    def metadata(self) -> Dict[str, Dict[str, Any]]:
        """Return a copy of per-key metadata (e.g. inline comments)."""
        return {k: dict(v) for k, v in self._meta.items()}

    def to_dict(self) -> Dict[str, str]:
        return dict(self._data)

    def __len__(self) -> int:
        return len(self._data)

    def __contains__(self, key: object) -> bool:
        return key in self._data
