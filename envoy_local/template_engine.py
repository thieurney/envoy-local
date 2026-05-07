"""Template engine for generating .env files from a template with placeholders."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

PLACEHOLDER_RE = re.compile(r"\{\{\s*([A-Z0-9_]+)\s*\}\}")


@dataclass
class TemplateRenderResult:
    rendered: str
    missing_keys: List[str] = field(default_factory=list)
    filled_keys: List[str] = field(default_factory=list)

    @property
    def is_complete(self) -> bool:
        return len(self.missing_keys) == 0

    def summary(self) -> str:
        parts = [f"Filled: {len(self.filled_keys)}"]
        if self.missing_keys:
            parts.append(f"Missing: {', '.join(self.missing_keys)}")
        return " | ".join(parts)


class TemplateEngine:
    """Renders .env templates by substituting {{ KEY }} placeholders."""

    def __init__(self, strict: bool = False) -> None:
        """Args:
            strict: If True, raise ValueError when placeholders are unresolved.
        """
        self.strict = strict

    def render(self, template: str, values: Dict[str, str]) -> TemplateRenderResult:
        """Render a template string using the provided values dict."""
        missing: List[str] = []
        filled: List[str] = []

        def replacer(match: re.Match) -> str:
            key = match.group(1)
            if key in values:
                filled.append(key)
                return values[key]
            missing.append(key)
            return match.group(0)  # leave placeholder intact

        rendered = PLACEHOLDER_RE.sub(replacer, template)

        if self.strict and missing:
            raise ValueError(f"Unresolved template placeholders: {missing}")

        return TemplateRenderResult(
            rendered=rendered,
            missing_keys=missing,
            filled_keys=filled,
        )

    def extract_placeholders(self, template: str) -> List[str]:
        """Return all unique placeholder keys found in the template."""
        return list(dict.fromkeys(PLACEHOLDER_RE.findall(template)))

    def render_from_file(self, template_path: str, values: Dict[str, str]) -> TemplateRenderResult:
        """Load a template from disk and render it."""
        with open(template_path, "r", encoding="utf-8") as fh:
            template = fh.read()
        return self.render(template, values)
