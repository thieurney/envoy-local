"""Tests for EnvFile loading/saving and SecretMasker functionality."""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from envoy_local.env_file import EnvFile, _strip_quotes
from envoy_local.secret_mask import SecretMasker, MASK_PLACEHOLDER


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    content = textwrap.dedent("""\
        # App settings
        APP_NAME=envoy-local
        DEBUG=true
        DB_PASSWORD=supersecret
        API_KEY="abc123xyz"
        PORT=8080
    """)
    p = tmp_path / ".env"
    p.write_text(content, encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# EnvFile tests
# ---------------------------------------------------------------------------

class TestEnvFile:
    def test_load_parses_keys(self, env_file: Path) -> None:
        ef = EnvFile(env_file).load()
        assert ef.get("APP_NAME") == "envoy-local"
        assert ef.get("DEBUG") == "true"
        assert ef.get("PORT") == "8080"

    def test_load_strips_quotes(self, env_file: Path) -> None:
        ef = EnvFile(env_file).load()
        assert ef.get("API_KEY") == "abc123xyz"

    def test_get_missing_key_returns_default(self, env_file: Path) -> None:
        ef = EnvFile(env_file).load()
        assert ef.get("MISSING", "fallback") == "fallback"

    def test_set_and_save_new_key(self, env_file: Path) -> None:
        ef = EnvFile(env_file).load()
        ef.set("NEW_VAR", "hello")
        ef.save()
        reloaded = EnvFile(env_file).load()
        assert reloaded.get("NEW_VAR") == "hello"

    def test_set_and_save_existing_key(self, env_file: Path) -> None:
        ef = EnvFile(env_file).load()
        ef.set("PORT", "9090")
        ef.save()
        reloaded = EnvFile(env_file).load()
        assert reloaded.get("PORT") == "9090"

    def test_delete_key(self, env_file: Path) -> None:
        ef = EnvFile(env_file).load()
        deleted = ef.delete("DEBUG")
        assert deleted is True
        assert ef.get("DEBUG") is None

    def test_delete_missing_key_returns_false(self, env_file: Path) -> None:
        ef = EnvFile(env_file).load()
        assert ef.delete("NONEXISTENT") is False

    def test_file_not_found_raises(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            EnvFile(tmp_path / "missing.env").load()


# ---------------------------------------------------------------------------
# SecretMasker tests
# ---------------------------------------------------------------------------

class TestSecretMasker:
    def test_masks_password(self) -> None:
        masker = SecretMasker()
        assert masker.mask("DB_PASSWORD", "secret") == MASK_PLACEHOLDER

    def test_masks_api_key(self) -> None:
        masker = SecretMasker()
        assert masker.mask("API_KEY", "abc123") == MASK_PLACEHOLDER

    def test_does_not_mask_plain_key(self) -> None:
        masker = SecretMasker()
        assert masker.mask("APP_NAME", "envoy") == "envoy"

    def test_reveal_chars(self) -> None:
        masker = SecretMasker(reveal_chars=3)
        result = masker.mask("DB_PASSWORD", "supersecret")
        assert result.startswith("sup")
        assert MASK_PLACEHOLDER in result

    def test_mask_dict(self, env_file: Path) -> None:
        ef = EnvFile(env_file).load()
        masker = SecretMasker()
        masked = masker.mask_dict(ef.entries)
        assert masked["DB_PASSWORD"] == MASK_PLACEHOLDER
        assert masked["API_KEY"] == MASK_PLACEHOLDER
        assert masked["APP_NAME"] == "envoy-local"

    def test_add_custom_pattern(self) -> None:
        masker = SecretMasker()
        masker.add_pattern(r'.*CUSTOM_SENSITIVE.*')
        assert masker.is_secret("MY_CUSTOM_SENSITIVE_FIELD") is True


# ---------------------------------------------------------------------------
# _strip_quotes helper
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("raw,expected", [
    ('"hello"', 'hello'),
    ("'world'", 'world'),
    ('no_quotes', 'no_quotes'),
    ('"mismatched\'', '"mismatched\''),
])
def test_strip_quotes(raw: str, expected: str) -> None:
    assert _strip_quotes(raw) == expected
