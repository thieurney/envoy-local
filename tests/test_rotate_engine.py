"""Tests for RotateEngine and RotateResult."""

import pytest

from envoy_local.env_file import EnvFile
from envoy_local.rotate_engine import RotateEngine, RotateResult


@pytest.fixture()
def env_file(tmp_path):
    path = tmp_path / ".env"
    path.write_text(
        "DATABASE_URL=postgres://localhost/db\n"
        "SECRET_KEY=old_secret\n"
        "API_TOKEN=old_token\n"
        "DEBUG=true\n"
    )
    ef = EnvFile(str(path))
    ef.load()
    return ef


@pytest.fixture()
def engine():
    return RotateEngine(generator=lambda: "NEW_GENERATED_VALUE")


class TestRotateResult:
    def test_success_when_no_errors(self):
        r = RotateResult(rotated=["SECRET_KEY"])
        assert r.success is True

    def test_failure_when_errors_present(self):
        r = RotateResult(errors={"MISSING_KEY": "Key not found in env file"})
        assert r.success is False

    def test_summary_shows_rotated_count(self):
        r = RotateResult(rotated=["A", "B"])
        assert "Rotated: 2" in r.summary()

    def test_summary_includes_skipped_when_present(self):
        r = RotateResult(rotated=["A"], skipped=["DEBUG"])
        assert "Skipped: 1" in r.summary()

    def test_summary_includes_errors_when_present(self):
        r = RotateResult(errors={"X": "not found"})
        assert "Errors: 1" in r.summary()

    def test_repr_contains_fields(self):
        r = RotateResult(rotated=["SECRET_KEY"])
        assert "SECRET_KEY" in repr(r)


class TestRotateEngine:
    def test_rotates_secret_keys_by_default(self, env_file, engine):
        result = engine.rotate(env_file)
        assert "SECRET_KEY" in result.rotated
        assert "API_TOKEN" in result.rotated

    def test_non_secret_keys_skipped_when_only_secrets(self, env_file, engine):
        result = engine.rotate(env_file, only_secrets=True)
        assert "DEBUG" in result.skipped
        assert "DATABASE_URL" in result.skipped

    def test_rotates_all_keys_when_only_secrets_false(self, env_file, engine):
        result = engine.rotate(env_file, only_secrets=False)
        assert len(result.skipped) == 0
        assert len(result.rotated) == 4

    def test_rotate_updates_value_in_env_file(self, env_file, engine):
        engine.rotate(env_file, keys=["SECRET_KEY"], only_secrets=False)
        assert env_file.get("SECRET_KEY") == "NEW_GENERATED_VALUE"

    def test_dry_run_does_not_modify_env_file(self, env_file, engine):
        engine.rotate(env_file, keys=["SECRET_KEY"], only_secrets=False, dry_run=True)
        assert env_file.get("SECRET_KEY") == "old_secret"

    def test_dry_run_still_reports_rotated(self, env_file, engine):
        result = engine.rotate(env_file, keys=["SECRET_KEY"], only_secrets=False, dry_run=True)
        assert "SECRET_KEY" in result.rotated

    def test_missing_key_recorded_as_error(self, env_file, engine):
        result = engine.rotate(env_file, keys=["NONEXISTENT"], only_secrets=False)
        assert "NONEXISTENT" in result.errors
        assert result.success is False

    def test_custom_generator_is_used(self, env_file):
        custom_engine = RotateEngine(generator=lambda: "CUSTOM_SECRET_XYZ")
        custom_engine.rotate(env_file, keys=["SECRET_KEY"], only_secrets=False)
        assert env_file.get("SECRET_KEY") == "CUSTOM_SECRET_XYZ"
