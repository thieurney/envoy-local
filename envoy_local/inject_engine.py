"""Engine for injecting env variables into a process environment or shell export block."""
from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envoy_local.env_file import EnvFile
from envoy_local.secret_mask import SecretMasker


@dataclass
class InjectResult:
    injected: List[str] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)
    error: Optional[str] = None

    @property
    def success(self) -> bool:
        return self.error is None

    def summary(self) -> str:
        parts = [f"Injected {len(self.injected)} variable(s)"]
        if self.skipped:
            parts.append(f"skipped {len(self.skipped)} (already set)")
        if self.error:
            parts.append(f"error: {self.error}")
        return ", ".join(parts)

    def __repr__(self) -> str:  # pragma: no cover
        return f"InjectResult(injected={len(self.injected)}, skipped={len(self.skipped)}, success={self.success})"


class InjectEngine:
    """Inject variables from an EnvFile into a subprocess environment."""

    def __init__(self, masker: Optional[SecretMasker] = None) -> None:
        self._masker = masker or SecretMasker()

    def build_env(self, env_file: EnvFile, overwrite: bool = False) -> Dict[str, str]:
        """Return os.environ merged with env_file values."""
        merged = dict(os.environ)
        for key, value in env_file.all().items():
            if key in merged and not overwrite:
                continue
            merged[key] = value
        return merged

    def inject(self, env_file: EnvFile, overwrite: bool = False) -> InjectResult:
        """Inject env_file variables into the current process environment."""
        result = InjectResult()
        try:
            for key, value in env_file.all().items():
                if key in os.environ and not overwrite:
                    result.skipped.append(key)
                else:
                    os.environ[key] = value
                    result.injected.append(key)
        except Exception as exc:  # pragma: no cover
            result.error = str(exc)
        return result

    def run_with_env(self, env_file: EnvFile, command: List[str], overwrite: bool = False) -> subprocess.CompletedProcess:  # type: ignore[type-arg]
        """Run a subprocess with the merged environment."""
        merged = self.build_env(env_file, overwrite=overwrite)
        return subprocess.run(command, env=merged, check=False)

    def export_shell(self, env_file: EnvFile, mask_secrets: bool = False) -> str:
        """Return a shell-export block string for the env file."""
        lines = []
        for key, value in env_file.all().items():
            display = self._masker.mask(key, value) if mask_secrets else value
            escaped = display.replace('"', '\\"')
            lines.append(f'export {key}="{escaped}"')
        return "\n".join(lines)
