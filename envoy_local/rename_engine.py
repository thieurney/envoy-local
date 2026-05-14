from dataclasses import dataclass, field
from typing import Optional
from envoy_local.env_file import EnvFile
from envoy_local.audit_log import AuditLog


@dataclass
class RenameResult:
    old_key: str
    new_key: str
    error: Optional[str] = None

    @property
    def success(self) -> bool:
        return self.error is None

    def summary(self) -> str:
        if self.success:
            return f"Renamed '{self.old_key}' -> '{self.new_key}'"
        return f"Failed to rename '{self.old_key}': {self.error}"

    def __repr__(self) -> str:
        status = "ok" if self.success else "error"
        return f"<RenameResult {self.old_key}->{self.new_key} [{status}]>"


class RenameEngine:
    def __init__(self, audit_log: Optional[AuditLog] = None):
        self._audit = audit_log

    def rename(self, env_file: EnvFile, old_key: str, new_key: str) -> RenameResult:
        """Rename a key in the given EnvFile, optionally logging the action."""
        if old_key not in env_file:
            return RenameResult(
                old_key=old_key,
                new_key=new_key,
                error=f"Key '{old_key}' not found",
            )

        if new_key in env_file and new_key != old_key:
            return RenameResult(
                old_key=old_key,
                new_key=new_key,
                error=f"Key '{new_key}' already exists",
            )

        value = env_file.get(old_key)
        env_file.set(new_key, value)
        env_file.delete(old_key)

        if self._audit is not None:
            self._audit.record(
                action="rename",
                key=old_key,
                detail=f"renamed to '{new_key}'",
            )

        return RenameResult(old_key=old_key, new_key=new_key)

    def rename_many(
        self, env_file: EnvFile, mapping: dict[str, str]
    ) -> list[RenameResult]:
        """Rename multiple keys given a {old_key: new_key} mapping."""
        results = []
        for old_key, new_key in mapping.items():
            result = self.rename(env_file, old_key, new_key)
            results.append(result)
        return results
