from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional
import re

from envoy_local.env_file import EnvFile


@dataclass
class SearchMatch:
    key: str
    value: str
    file_path: str
    line_number: Optional[int] = None

    def __repr__(self) -> str:
        loc = f":{self.line_number}" if self.line_number is not None else ""
        return f"<SearchMatch {self.file_path}{loc} {self.key}={self.value!r}>"


@dataclass
class SearchResult:
    matches: List[SearchMatch] = field(default_factory=list)
    query: str = ""

    @property
    def found(self) -> bool:
        return len(self.matches) > 0

    @property
    def count(self) -> int:
        return len(self.matches)

    def summary(self) -> str:
        if not self.found:
            return f"No matches found for '{self.query}'."
        return f"Found {self.count} match(es) for '{self.query}'."


class SearchEngine:
    def __init__(self, case_sensitive: bool = False, search_values: bool = True, search_keys: bool = True):
        self.case_sensitive = case_sensitive
        self.search_values = search_values
        self.search_keys = search_keys

    def search(self, env_files: List[EnvFile], query: str, use_regex: bool = False) -> SearchResult:
        matches: List[SearchMatch] = []
        flags = 0 if self.case_sensitive else re.IGNORECASE

        try:
            pattern = re.compile(query if use_regex else re.escape(query), flags)
        except re.error as exc:
            raise ValueError(f"Invalid regex pattern '{query}': {exc}") from exc

        for env_file in env_files:
            file_path = str(env_file.path)
            for key, value in env_file.all().items():
                matched = False
                if self.search_keys and pattern.search(key):
                    matched = True
                if self.search_values and pattern.search(value):
                    matched = True
                if matched:
                    line_number = self._find_line(env_file, key)
                    matches.append(SearchMatch(
                        key=key,
                        value=value,
                        file_path=file_path,
                        line_number=line_number,
                    ))

        return SearchResult(matches=matches, query=query)

    def _find_line(self, env_file: EnvFile, target_key: str) -> Optional[int]:
        try:
            lines = env_file.path.read_text().splitlines()
            for i, line in enumerate(lines, start=1):
                stripped = line.strip()
                if stripped.startswith("#") or "=" not in stripped:
                    continue
                k = stripped.split("=", 1)[0].strip()
                if k == target_key:
                    return i
        except Exception:
            pass
        return None
