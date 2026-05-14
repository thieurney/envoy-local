"""Engine for stripping comments and blank lines from .env files."""

from dataclasses import dataclass, field
from typing import List

from envoy_local.env_file import EnvFile


@dataclass
class StripResult:
    path: str
    lines_before: int
    lines_after: int
    comments_removed: int
    blanks_removed: int
    error: str = ""

    @property
    def success(self) -> bool:
        return not self.error

    @property
    def summary(self) -> str:
        if not self.success:
            return f"strip failed for {self.path}: {self.error}"
        saved = self.lines_before - self.lines_after
        return (
            f"stripped {self.path}: removed {self.comments_removed} comment(s) "
            f"and {self.blanks_removed} blank line(s) ({saved} lines total)"
        )

    def __repr__(self) -> str:
        return (
            f"StripResult(path={self.path!r}, success={self.success}, "
            f"comments_removed={self.comments_removed}, blanks_removed={self.blanks_removed})"
        )


class StripEngine:
    """Strips comments and/or blank lines from an EnvFile."""

    def __init__(self, remove_comments: bool = True, remove_blanks: bool = True):
        self.remove_comments = remove_comments
        self.remove_blanks = remove_blanks

    def strip(self, env_file: EnvFile, dry_run: bool = False) -> StripResult:
        try:
            original_lines = env_file.raw_lines if hasattr(env_file, "raw_lines") else self._read_lines(env_file)
        except Exception as exc:
            return StripResult(
                path=str(env_file.path),
                lines_before=0,
                lines_after=0,
                comments_removed=0,
                blanks_removed=0,
                error=str(exc),
            )

        comments_removed = 0
        blanks_removed = 0
        kept: List[str] = []

        for line in original_lines:
            stripped = line.strip()
            if self.remove_comments and stripped.startswith("#"):
                comments_removed += 1
                continue
            if self.remove_blanks and stripped == "":
                blanks_removed += 1
                continue
            kept.append(line)

        result = StripResult(
            path=str(env_file.path),
            lines_before=len(original_lines),
            lines_after=len(kept),
            comments_removed=comments_removed,
            blanks_removed=blanks_removed,
        )

        if not dry_run and result.success:
            try:
                env_file.path.write_text("".join(kept))
            except Exception as exc:
                result.error = str(exc)

        return result

    def _read_lines(self, env_file: EnvFile) -> List[str]:
        return env_file.path.read_text().splitlines(keepends=True)
