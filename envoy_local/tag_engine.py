"""Tag engine: attach and query metadata tags on .env keys."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envoy_local.env_file import EnvFile


@dataclass
class TagResult:
    tagged: List[str] = field(default_factory=list)
    untagged: List[str] = field(default_factory=list)
    error: Optional[str] = None

    @property
    def success(self) -> bool:
        return self.error is None

    def summary(self) -> str:
        if not self.success:
            return f"Tag operation failed: {self.error}"
        parts = []
        if self.tagged:
            parts.append(f"Tagged {len(self.tagged)} key(s): {', '.join(self.tagged)}")
        if self.untagged:
            parts.append(f"Removed tag from {len(self.untagged)} key(s): {', '.join(self.untagged)}")
        return "; ".join(parts) if parts else "No changes made."

    def __repr__(self) -> str:
        return f"TagResult(success={self.success}, tagged={self.tagged}, untagged={self.untagged})"


class TagEngine:
    """Manages a sidecar tag file (.env.tags) that stores key->tag mappings."""

    TAG_SUFFIX = ".tags"

    def __init__(self, env_file: EnvFile) -> None:
        self._env = env_file
        self._tag_path = str(env_file.path) + self.TAG_SUFFIX
        self._tags: Dict[str, List[str]] = self._load_tags()

    # ------------------------------------------------------------------
    def _load_tags(self) -> Dict[str, List[str]]:
        import json, pathlib
        p = pathlib.Path(self._tag_path)
        if not p.exists():
            return {}
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def _save_tags(self) -> None:
        import json, pathlib
        pathlib.Path(self._tag_path).write_text(
            json.dumps(self._tags, indent=2), encoding="utf-8"
        )

    # ------------------------------------------------------------------
    def add_tag(self, keys: List[str], tag: str, dry_run: bool = False) -> TagResult:
        """Attach *tag* to each key that exists in the env file."""
        result = TagResult()
        env_keys = set(self._env.all_keys())
        for key in keys:
            if key not in env_keys:
                result.error = f"Key '{key}' not found in env file"
                return result
            bucket = self._tags.setdefault(key, [])
            if tag not in bucket:
                bucket.append(tag)
                result.tagged.append(key)
        if not dry_run and result.tagged:
            self._save_tags()
        return result

    def remove_tag(self, keys: List[str], tag: str, dry_run: bool = False) -> TagResult:
        """Detach *tag* from each key."""
        result = TagResult()
        for key in keys:
            bucket = self._tags.get(key, [])
            if tag in bucket:
                bucket.remove(tag)
                result.untagged.append(key)
                if not bucket:
                    del self._tags[key]
        if not dry_run and result.untagged:
            self._save_tags()
        return result

    def keys_for_tag(self, tag: str) -> List[str]:
        """Return all keys that carry *tag*."""
        return [k for k, tags in self._tags.items() if tag in tags]

    def tags_for_key(self, key: str) -> List[str]:
        """Return all tags attached to *key*."""
        return list(self._tags.get(key, []))
