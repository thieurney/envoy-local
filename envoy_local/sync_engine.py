"""Sync engine for propagating .env changes across registered projects."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from envoy_local.env_file import EnvFile
from envoy_local.diff_engine import DiffEngine, DiffResult
from envoy_local.project_registry import ProjectRegistry


@dataclass
class SyncResult:
    project_name: str
    project_path: str
    diff: DiffResult
    applied: bool = False
    error: Optional[str] = None

    @property
    def success(self) -> bool:
        return self.applied and self.error is None


@dataclass
class SyncReport:
    source: str
    results: List[SyncResult] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.results)

    @property
    def synced(self) -> int:
        return sum(1 for r in self.results if r.success)

    @property
    def skipped(self) -> int:
        return sum(1 for r in self.results if not r.diff.has_changes)

    @property
    def failed(self) -> int:
        return sum(1 for r in self.results if r.error is not None)

    def summary(self) -> str:
        return (
            f"Sync from '{self.source}': "
            f"{self.synced} synced, {self.skipped} skipped, {self.failed} failed "
            f"(total: {self.total})"
        )


class SyncEngine:
    def __init__(self, registry: ProjectRegistry):
        self.registry = registry
        self._diff_engine = DiffEngine()

    def sync(self, source_path: str, dry_run: bool = False) -> SyncReport:
        source_env = EnvFile(source_path)
        source_env.load()
        report = SyncReport(source=source_path)

        for name, info in self.registry.list_projects().items():
            target_path = info.get("path", "")
            result = self._sync_project(name, target_path, source_env, dry_run)
            report.results.append(result)

        return report

    def _sync_project(self, name: str, path: str, source: EnvFile, dry_run: bool) -> SyncResult:
        try:
            target_env = EnvFile(path)
            if Path(path).exists():
                target_env.load()

            diff = self._diff_engine.compare(source, target_env)

            if not diff.has_changes:
                return SyncResult(project_name=name, project_path=path, diff=diff, applied=False)

            if not dry_run:
                for key in diff.added + diff.modified:
                    target_env.set(key, source.get(key))
                target_env.save()

            return SyncResult(project_name=name, project_path=path, diff=diff, applied=not dry_run)
        except Exception as exc:
            from envoy_local.diff_engine import DiffResult
            empty_diff = DiffResult(added=[], removed=[], modified=[], unchanged=[])
            return SyncResult(project_name=name, project_path=path, diff=empty_diff, error=str(exc))
