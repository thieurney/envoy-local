"""Tests for the lint engine."""

import pytest
from unittest.mock import MagicMock
from envoy_local.lint_engine import LintEngine, LintResult, LintIssue
from envoy_local.env_file import EnvFile


@pytest.fixture
def make_env(tmp_path):
    def _make(contents: dict) -> EnvFile:
        env = MagicMock(spec=EnvFile)
        env.all.return_value = contents
        return env
    return _make


class TestLintResult:
    def test_is_clean_when_no_issues(self):
        result = LintResult()
        assert result.is_clean is True

    def test_is_not_clean_with_issues(self):
        result = LintResult(issues=[LintIssue(key="X", message="bad")])
        assert result.is_clean is False

    def test_error_count(self):
        result = LintResult(issues=[
            LintIssue(key="A", message="err", severity="error"),
            LintIssue(key="B", message="warn", severity="warning"),
        ])
        assert result.error_count == 1
        assert result.warning_count == 1

    def test_summary_clean(self):
        assert LintResult().summary() == "No lint issues found."

    def test_summary_with_issues(self):
        result = LintResult(issues=[
            LintIssue(key="A", message="e", severity="error"),
            LintIssue(key="B", message="w", severity="warning"),
        ])
        summary = result.summary()
        assert "1 error" in summary
        assert "1 warning" in summary

    def test_lint_issue_repr(self):
        issue = LintIssue(key="FOO", message="test msg", severity="error")
        assert "ERROR" in repr(issue)
        assert "FOO" in repr(issue)


class TestLintEngine:
    def test_clean_env_has_no_issues(self, make_env):
        env = make_env({"DATABASE_URL": "postgres://localhost/db", "APP_PORT": "8080"})
        engine = LintEngine(env)
        result = engine.run()
        assert result.is_clean

    def test_detects_lowercase_key(self, make_env):
        env = make_env({"database_url": "value"})
        result = LintEngine(env).run()
        assert not result.is_clean
        assert any("SCREAMING_SNAKE_CASE" in i.message for i in result.issues)

    def test_detects_empty_value(self, make_env):
        env = make_env({"API_KEY": ""})
        result = LintEngine(env).run()
        assert not result.is_clean
        assert any("empty" in i.message for i in result.issues)

    def test_detects_leading_whitespace(self, make_env):
        env = make_env({"SECRET": "  value"})
        result = LintEngine(env).run()
        issues = [i for i in result.issues if i.severity == "error"]
        assert any("whitespace" in i.message for i in issues)

    def test_detects_trailing_whitespace(self, make_env):
        env = make_env({"SECRET": "value  "})
        result = LintEngine(env).run()
        issues = [i for i in result.issues if i.severity == "error"]
        assert any("whitespace" in i.message for i in issues)

    def test_detects_long_key(self, make_env):
        long_key = "A" * 65
        env = make_env({long_key: "value"})
        result = LintEngine(env).run()
        assert any("too long" in i.message for i in result.issues)

    def test_multiple_issues_on_single_key(self, make_env):
        env = make_env({"bad_key": ""})
        result = LintEngine(env).run()
        keys_with_issues = [i.key for i in result.issues]
        assert keys_with_issues.count("bad_key") >= 2
