import pytest
from pathlib import Path
from unittest.mock import MagicMock

from envoy_local.search_engine import SearchEngine, SearchMatch, SearchResult
from envoy_local.env_file import EnvFile


def _make_env(tmp_path: Path, name: str, data: dict) -> EnvFile:
    p = tmp_path / name
    lines = "\n".join(f"{k}={v}" for k, v in data.items())
    p.write_text(lines)
    ef = EnvFile(p)
    ef.load()
    return ef


@pytest.fixture
def tmp_env(tmp_path):
    return _make_env(tmp_path, ".env", {
        "DATABASE_URL": "postgres://localhost/mydb",
        "SECRET_KEY": "supersecret",
        "DEBUG": "true",
    })


@pytest.fixture
def engine():
    return SearchEngine()


class TestSearchResult:
    def test_found_false_when_empty(self):
        r = SearchResult(query="x")
        assert r.found is False

    def test_found_true_when_matches(self):
        m = SearchMatch(key="K", value="V", file_path=".env")
        r = SearchResult(matches=[m], query="K")
        assert r.found is True

    def test_count_reflects_matches(self):
        matches = [SearchMatch(key=f"K{i}", value="v", file_path=".env") for i in range(3)]
        r = SearchResult(matches=matches, query="K")
        assert r.count == 3

    def test_summary_no_matches(self):
        r = SearchResult(query="ghost")
        assert "No matches" in r.summary()
        assert "ghost" in r.summary()

    def test_summary_with_matches(self):
        m = SearchMatch(key="A", value="B", file_path=".env")
        r = SearchResult(matches=[m], query="A")
        assert "1 match" in r.summary()


class TestSearchEngine:
    def test_finds_key_by_substring(self, engine, tmp_env):
        result = engine.search([tmp_env], "SECRET")
        assert result.found
        assert any(m.key == "SECRET_KEY" for m in result.matches)

    def test_finds_value_by_substring(self, engine, tmp_env):
        result = engine.search([tmp_env], "postgres")
        assert result.found
        assert any(m.key == "DATABASE_URL" for m in result.matches)

    def test_case_insensitive_by_default(self, engine, tmp_env):
        result = engine.search([tmp_env], "debug")
        assert result.found

    def test_case_sensitive_no_match(self, tmp_env):
        eng = SearchEngine(case_sensitive=True)
        result = eng.search([tmp_env], "debug")
        assert not result.found

    def test_keys_only_skips_value_match(self, tmp_env):
        eng = SearchEngine(search_values=False, search_keys=True)
        result = eng.search([tmp_env], "postgres")
        assert not result.found

    def test_values_only_skips_key_match(self, tmp_env):
        eng = SearchEngine(search_values=True, search_keys=False)
        result = eng.search([tmp_env], "SECRET_KEY")
        assert not result.found

    def test_regex_search(self, engine, tmp_env):
        result = engine.search([tmp_env], r"^DEBUG$", use_regex=True)
        assert result.found

    def test_invalid_regex_raises_value_error(self, engine, tmp_env):
        with pytest.raises(ValueError, match="Invalid regex"):
            engine.search([tmp_env], "[unclosed", use_regex=True)

    def test_line_number_is_set(self, engine, tmp_env):
        result = engine.search([tmp_env], "DEBUG")
        match = next(m for m in result.matches if m.key == "DEBUG")
        assert match.line_number is not None
        assert match.line_number >= 1

    def test_searches_multiple_files(self, tmp_path):
        ef1 = _make_env(tmp_path, ".env.a", {"FOO": "bar"})
        ef2 = _make_env(tmp_path, ".env.b", {"FOO": "baz"})
        eng = SearchEngine()
        result = eng.search([ef1, ef2], "FOO")
        assert result.count == 2
