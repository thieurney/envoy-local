"""Lint engine for validating .env file style and best practices."""

from dataclasses import dataclass, field
from typing import List
from envoy_local.env_file import EnvFile


@dataclass
class LintIssue:
    key: str
    message: str
    severity: str = "warning"  # "warning" or "error"

    def __repr__(self) -> str:
        return f"[{self.severity.upper()}] {self.key}: {self.message}"


@dataclass
class LintResult:
    issues: List[LintIssue] = field(default_factory=list)

    @property
    def is_clean(self) -> bool:
        return len(self.issues) == 0

    @property
    def error_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == "error")

    @property
    def warning_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == "warning")

    def summary(self) -> str:
        if self.is_clean:
            return "No lint issues found."
        parts = []
        if self.error_count:
            parts.append(f"{self.error_count} error(s)")
        if self.warning_count:
            parts.append(f"{self.warning_count} warning(s)")
        return "Lint issues: " + ", ".join(parts) + "."


class LintEngine:
    SCREAMING_SNAKE = __import__("re").compile(r"^[A-Z][A-Z0-9_]*$")

    def __init__(self, env_file: EnvFile):
        self.env_file = env_file

    def run(self) -> LintResult:
        result = LintResult()
        data = self.env_file.all()

        for key, value in data.items():
            self._check_key_naming(key, result)
            self._check_empty_value(key, value, result)
            self._check_whitespace_in_value(key, value, result)
            self._check_key_length(key, result)

        return result

    def _check_key_naming(self, key: str, result: LintResult) -> None:
        if not self.SCREAMING_SNAKE.match(key):
            result.issues.append(LintIssue(
                key=key,
                message="Key should use SCREAMING_SNAKE_CASE (uppercase letters, digits, underscores).",
                severity="warning",
            ))

    def _check_empty_value(self, key: str, value: str, result: LintResult) -> None:
        if value == "":
            result.issues.append(LintIssue(
                key=key,
                message="Value is empty. Consider removing this key or providing a placeholder.",
                severity="warning",
            ))

    def _check_whitespace_in_value(self, key: str, value: str, result: LintResult) -> None:
        if value != value.strip():
            result.issues.append(LintIssue(
                key=key,
                message="Value has leading or trailing whitespace.",
                severity="error",
            ))

    def _check_key_length(self, key: str, result: LintResult) -> None:
        if len(key) > 64:
            result.issues.append(LintIssue(
                key=key,
                message=f"Key name is too long ({len(key)} chars). Consider keeping keys under 64 characters.",
                severity="warning",
            ))
