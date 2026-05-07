"""Validation engine for checking .env files against required key schemas."""

from dataclasses import dataclass, field
from typing import List, Optional
from envoy_local.env_file import EnvFile


@dataclass
class ValidationResult:
    missing_keys: List[str] = field(default_factory=list)
    empty_keys: List[str] = field(default_factory=list)
    unexpected_keys: List[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return not self.missing_keys and not self.empty_keys

    def summary(self) -> str:
        parts = []
        if self.missing_keys:
            parts.append(f"Missing keys ({len(self.missing_keys)}): {', '.join(self.missing_keys)}")
        if self.empty_keys:
            parts.append(f"Empty keys ({len(self.empty_keys)}): {', '.join(self.empty_keys)}")
        if self.unexpected_keys:
            parts.append(f"Unexpected keys ({len(self.unexpected_keys)}): {', '.join(self.unexpected_keys)}")
        if not parts:
            return "All required keys are present and non-empty."
        return " | ".join(parts)


class ValidateEngine:
    """Validates an EnvFile against a list of required keys."""

    def __init__(self, required_keys: List[str], allow_extra: bool = True):
        self.required_keys = required_keys
        self.allow_extra = allow_extra

    def validate(self, env_file: EnvFile) -> ValidationResult:
        result = ValidationResult()
        env_keys = set(env_file.keys())
        required_set = set(self.required_keys)

        for key in self.required_keys:
            if key not in env_keys:
                result.missing_keys.append(key)
            elif not env_file.get(key, "").strip():
                result.empty_keys.append(key)

        if not self.allow_extra:
            for key in env_keys:
                if key not in required_set:
                    result.unexpected_keys.append(key)

        result.missing_keys.sort()
        result.empty_keys.sort()
        result.unexpected_keys.sort()
        return result

    def validate_from_schema_file(self, schema_path: str, env_file: EnvFile) -> ValidationResult:
        """Load required keys from a plain text schema file (one key per line)."""
        with open(schema_path, "r") as f:
            keys = [
                line.strip()
                for line in f
                if line.strip() and not line.strip().startswith("#")
            ]
        self.required_keys = keys
        return self.validate(env_file)
