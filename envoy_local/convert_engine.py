"""Convert .env files between different formats (dotenv, json, yaml, shell export)."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Optional

from envoy_local.env_file import EnvFile

SUPPORTED_FORMATS = ("dotenv", "json", "yaml", "shell")


@dataclass
class ConvertResult:
    format: str
    output: str
    error: Optional[str] = None
    keys_converted: int = 0

    @property
    def success(self) -> bool:
        return self.error is None

    def summary(self) -> str:
        if not self.success:
            return f"Conversion failed: {self.error}"
        return f"Converted {self.keys_converted} key(s) to {self.format} format."

    def __repr__(self) -> str:
        return f"<ConvertResult format={self.format!r} keys={self.keys_converted} success={self.success}>"


class ConvertEngine:
    def __init__(self, env_file: EnvFile) -> None:
        self._env = env_file

    def convert(self, fmt: str) -> ConvertResult:
        fmt = fmt.lower()
        if fmt not in SUPPORTED_FORMATS:
            return ConvertResult(
                format=fmt,
                output="",
                error=f"Unsupported format '{fmt}'. Choose from: {', '.join(SUPPORTED_FORMATS)}",
            )

        data = self._env.all()
        try:
            if fmt == "dotenv":
                output = self._to_dotenv(data)
            elif fmt == "json":
                output = self._to_json(data)
            elif fmt == "yaml":
                output = self._to_yaml(data)
            elif fmt == "shell":
                output = self._to_shell(data)
            else:
                output = ""
        except Exception as exc:  # pragma: no cover
            return ConvertResult(format=fmt, output="", error=str(exc))

        return ConvertResult(format=fmt, output=output, keys_converted=len(data))

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _to_dotenv(data: dict) -> str:
        lines = [f'{k}="{v}"' for k, v in data.items()]
        return "\n".join(lines)

    @staticmethod
    def _to_json(data: dict) -> str:
        return json.dumps(data, indent=2)

    @staticmethod
    def _to_yaml(data: dict) -> str:
        lines = [f"{k}: {json.dumps(v)}" for k, v in data.items()]
        return "\n".join(lines)

    @staticmethod
    def _to_shell(data: dict) -> str:
        lines = [f"export {k}={json.dumps(v)}" for k, v in data.items()]
        return "\n".join(lines)
