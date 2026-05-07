"""Tests for EncryptEngine and EncryptResult."""

import pytest
from pathlib import Path

from envoy_local.encrypt_engine import EncryptEngine, EncryptResult
from envoy_local.env_file import EnvFile


@pytest.fixture
def env_file(tmp_path) -> EnvFile:
    p = tmp_path / ".env"
    p.write_text("DB_HOST=localhost\nDB_PASS=supersecret\nAPI_KEY=abc123\n")
    ef = EnvFile(p)
    ef.load()
    return ef


@pytest.fixture
def engine() -> EncryptEngine:
    return EncryptEngine(passphrase="test-passphrase")


class TestEncryptResult:
    def test_success_when_no_errors(self):
        r = EncryptResult(encrypted={"A": "enc:xyz"}, skipped=[], errors=[])
        assert r.success is True

    def test_failure_when_errors_present(self):
        r = EncryptResult(errors=["Key not found: FOO"])
        assert r.success is False

    def test_summary_shows_encrypted_count(self):
        r = EncryptResult(encrypted={"A": "enc:x", "B": "enc:y"})
        assert "Encrypted: 2" in r.summary()

    def test_summary_shows_skipped_when_present(self):
        r = EncryptResult(encrypted={}, skipped=["A"])
        assert "Skipped: 1" in r.summary()

    def test_summary_shows_errors_when_present(self):
        r = EncryptResult(errors=["oops"])
        assert "Errors: 1" in r.summary()


class TestEncryptEngine:
    def test_encrypt_value_adds_marker(self, engine):
        enc = engine.encrypt_value("hello")
        assert enc.startswith("enc:")

    def test_decrypt_value_roundtrip(self, engine):
        original = "supersecret"
        enc = engine.encrypt_value(original)
        assert engine.decrypt_value(enc) == original

    def test_decrypt_returns_none_for_plain_text(self, engine):
        assert engine.decrypt_value("plaintext") is None

    def test_different_passphrases_produce_different_ciphertext(self):
        e1 = EncryptEngine("pass1")
        e2 = EncryptEngine("pass2")
        enc1 = e1.encrypt_value("value")
        enc2 = e2.encrypt_value("value")
        assert enc1 != enc2

    def test_encrypt_file_encrypts_all_keys(self, engine, env_file):
        result = engine.encrypt_file(env_file)
        assert result.success
        assert set(result.encrypted.keys()) == {"DB_HOST", "DB_PASS", "API_KEY"}

    def test_encrypt_file_specific_keys(self, engine, env_file):
        result = engine.encrypt_file(env_file, keys=["DB_PASS"])
        assert result.success
        assert "DB_PASS" in result.encrypted
        assert "DB_HOST" not in result.encrypted

    def test_encrypt_file_skips_already_encrypted(self, engine, env_file):
        env_file.set("API_KEY", engine.encrypt_value("abc123"))
        result = engine.encrypt_file(env_file, keys=["API_KEY"])
        assert "API_KEY" in result.skipped
        assert "API_KEY" not in result.encrypted

    def test_encrypt_file_errors_on_missing_key(self, engine, env_file):
        result = engine.encrypt_file(env_file, keys=["MISSING"])
        assert not result.success
        assert any("MISSING" in e for e in result.errors)

    def test_decrypt_file_restores_values(self, engine, env_file):
        engine.encrypt_file(env_file)
        for key, enc_val in engine.encrypt_file(env_file).encrypted.items():
            env_file.set(key, enc_val)
        decrypted = engine.decrypt_file(env_file)
        assert decrypted["DB_HOST"] == "localhost"
        assert decrypted["DB_PASS"] == "supersecret"
