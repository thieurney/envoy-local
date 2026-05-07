"""Export engine for serializing .env data to multiple formats."""

import json
from typing import Dict, Optional
from envoy_local.env_file import EnvFile
from envoy_local.secret_mask import SecretMasker


SUPPORTED_FORMATS = ("dotenv", "json", "shell")


class ExportEngine:
    """Handles exporting environment variables to various output formats."""

    def __init__(self, masker: Optional[SecretMasker] = None):
        self.masker = masker or SecretMasker()

    def export(self, env_file: EnvFile, fmt: str, mask_secrets: bool = False) -> str:
        """Export env data in the requested format.

        Args:
            env_file: Loaded EnvFile instance.
            fmt: One of 'dotenv', 'json', 'shell'.
            mask_secrets: If True, secret values are masked before export.

        Returns:
            A string representation in the requested format.
        """
        if fmt not in SUPPORTED_FORMATS:
            raise ValueError(f"Unsupported format '{fmt}'. Choose from: {SUPPORTED_FORMATS}")

        data: Dict[str, str] = dict(env_file.all())
        if mask_secrets:
            data = self.masker.mask_dict(data)

        if fmt == "dotenv":
            return self._to_dotenv(data)
        elif fmt == "json":
            return self._to_json(data)
        elif fmt == "shell":
            return self._to_shell(data)

    def _to_dotenv(self, data: Dict[str, str]) -> str:
        lines = []
        for key, value in data.items():
            escaped = value.replace('"', '\\"')
            lines.append(f'{key}="{escaped}"')
        return "\n".join(lines)

    def _to_json(self, data: Dict[str, str]) -> str:
        return json.dumps(data, indent=2)

    def _to_shell(self, data: Dict[str, str]) -> str:
        lines = []
        for key, value in data.items():
            escaped = value.replace("'", "'\"'\"'")
            lines.append(f"export {key}='{escaped}'")
        return "\n".join(lines)
