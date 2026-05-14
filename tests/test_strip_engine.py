"""Tests for StripEngine and StripResult."""

import pytest
from pathlib import Path

from envoy_local.env_file import EnvFile
from envoy_local.strip_engine import StripEngine, StripResult


@pytest.fixture
def env_file(tmp_path):
    p = tmp_path / ".env"
    p.write_text(
        "# This is a comment\n"
        "DB_HOST=localhost\n"
        "\n"
        "# Another comment\n"
        "DB_PORT=5432\n"
        "\n"
        "SECRET_KEY=abc123\n"
    )
    ef = EnvFile(p)
    ef.load()
    return ef


@pytest.fixture
def engine():
    return StripEngine()


class TestStripResult:
    def test_success_true_when_no_error(self):
        r = StripResult(path=".env", lines_before=5, lines_after=3, comments_removed=1, blanks_removed=1)
        assert r.success is True

    def test_success_false_when_error_set(self):
        r = StripResult(path=".env", lines_before=0, lines_after=0, comments_removed=0, blanks_removed=0, error="oops")
        assert r.success is False

    def test_summary_shows_counts(self):
        r = StripResult(path=".env", lines_before=7, lines_after=3, comments_removed=2, blanks_removed=2)
        assert "2 comment" in r.summary
        assert "2 blank" in r.summary

    def test_summary_shows_error_on_failure(self):
        r = StripResult(path=".env", lines_before=0, lines_after=0, comments_removed=0, blanks_removed=0, error="bad")
        assert "failed" in r.summary
        assert "bad" in r.summary

    def test_repr_contains_key_fields(self):
        r = StripResult(path=".env", lines_before=4, lines_after=2, comments_removed=1, blanks_removed=1)
        assert "StripResult" in repr(r)
        assert ".env" in repr(r)


class TestStripEngine:
    def test_removes_comments(self, env_file):
        engine = StripEngine(remove_comments=True, remove_blanks=False)
        result = engine.strip(env_file, dry_run=True)
        assert result.comments_removed == 2
        assert result.success

    def test_removes_blank_lines(self, env_file):
        engine = StripEngine(remove_comments=False, remove_blanks=True)
        result = engine.strip(env_file, dry_run=True)
        assert result.blanks_removed == 2
        assert result.success

    def test_removes_both_by_default(self, env_file):
        result = engine.strip(env_file, dry_run=True)
        assert result.comments_removed == 2
        assert result.blanks_removed == 2

    def test_dry_run_does_not_write(self, env_file):
        original = env_file.path.read_text()
        engine = StripEngine()
        engine.strip(env_file, dry_run=True)
        assert env_file.path.read_text() == original

    def test_writes_file_when_not_dry_run(self, env_file):
        original = env_file.path.read_text()
        engine = StripEngine()
        engine.strip(env_file, dry_run=False)
        new_content = env_file.path.read_text()
        assert new_content != original
        assert "#" not in new_content

    def test_lines_after_less_than_before(self, env_file):
        result = engine.strip(env_file, dry_run=True)
        assert result.lines_after < result.lines_before

    def test_error_on_unreadable_file(self, tmp_path):
        p = tmp_path / "missing.env"
        ef = EnvFile(p)
        ef.path = p  # file does not exist
        engine = StripEngine()
        result = engine.strip(ef, dry_run=True)
        assert not result.success
        assert result.error
