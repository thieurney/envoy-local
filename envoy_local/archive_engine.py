"""Archive engine: compress and store .env files as timestamped archives."""

from __future__ import annotations

import json
import zipfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from envoy_local.env_file import EnvFile


@dataclass
class ArchiveResult:
    archive_path: Optional[Path] = None
    source_path: Optional[Path] = None
    key_count: int = 0
    error: Optional[str] = None

    @property
    def success(self) -> bool:
        return self.error is None

    def summary(self) -> str:
        if not self.success:
            return f"Archive failed: {self.error}"
        return (
            f"Archived {self.key_count} key(s) from '{self.source_path}' "
            f"to '{self.archive_path}'"
        )

    def __repr__(self) -> str:
        return (
            f"ArchiveResult(success={self.success}, "
            f"key_count={self.key_count}, archive_path={self.archive_path})"
        )


class ArchiveEngine:
    """Compress an EnvFile into a zip archive with metadata."""

    def __init__(self, storage_dir: Path) -> None:
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def archive(self, env_file: EnvFile, label: str = "") -> ArchiveResult:
        """Write env_file contents into a timestamped zip archive."""
        try:
            ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            stem = Path(env_file.path).stem if env_file.path else "env"
            suffix = f"_{label}" if label else ""
            archive_name = f"{stem}{suffix}_{ts}.zip"
            archive_path = self.storage_dir / archive_name

            data = env_file.all()
            meta = {
                "source": str(env_file.path),
                "archived_at": ts,
                "label": label,
                "key_count": len(data),
            }

            with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as zf:
                env_lines = "\n".join(f"{k}={v}" for k, v in data.items())
                zf.writestr("env.txt", env_lines)
                zf.writestr("meta.json", json.dumps(meta, indent=2))

            return ArchiveResult(
                archive_path=archive_path,
                source_path=Path(env_file.path) if env_file.path else None,
                key_count=len(data),
            )
        except Exception as exc:  # pragma: no cover
            return ArchiveResult(error=str(exc))

    def list_archives(self) -> list[Path]:
        """Return all zip archives in the storage directory, newest first."""
        return sorted(
            self.storage_dir.glob("*.zip"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )

    def extract(self, archive_path: Path) -> dict[str, str]:
        """Extract and return key/value pairs from an archive."""
        result: dict[str, str] = {}
        with zipfile.ZipFile(archive_path, "r") as zf:
            raw = zf.read("env.txt").decode()
        for line in raw.splitlines():
            if "=" in line:
                k, _, v = line.partition("=")
                result[k.strip()] = v.strip()
        return result
