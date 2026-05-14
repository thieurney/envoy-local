import pytest
from unittest.mock import MagicMock
from envoy_local.env_file import EnvFile
from envoy_local.rename_engine import RenameEngine, RenameResult


@pytest.fixture
def env_file(tmp_path):
    p = tmp_path / ".env"
    p.write_text("DB_HOST=localhost\nDB_PORT=5432\nSECRET_KEY=abc123\n")
    ef = EnvFile(str(p))
    ef.load()
    return ef


@pytest.fixture
def engine():
    return RenameEngine()


class TestRenameResult:
    def test_success_true_when_no_error(self):
        r = RenameResult(old_key="A", new_key="B")
        assert r.success is True

    def test_success_false_when_error_set(self):
        r = RenameResult(old_key="A", new_key="B", error="not found")
        assert r.success is False

    def test_summary_on_success(self):
        r = RenameResult(old_key="OLD", new_key="NEW")
        assert "OLD" in r.summary()
        assert "NEW" in r.summary()

    def test_summary_on_failure(self):
        r = RenameResult(old_key="OLD", new_key="NEW", error="Key 'OLD' not found")
        assert "Failed" in r.summary()
        assert "OLD" in r.summary()

    def test_repr_contains_keys(self):
        r = RenameResult(old_key="A", new_key="B")
        assert "A->B" in repr(r)
        assert "ok" in repr(r)


class TestRenameEngine:
    def test_renames_existing_key(self, env_file, engine):
        result = engine.rename(env_file, "DB_HOST", "DATABASE_HOST")
        assert result.success
        assert env_file.get("DATABASE_HOST") == "localhost"
        assert "DB_HOST" not in env_file

    def test_error_when_key_not_found(self, env_file, engine):
        result = engine.rename(env_file, "MISSING_KEY", "NEW_KEY")
        assert not result.success
        assert "not found" in result.error

    def test_error_when_new_key_already_exists(self, env_file, engine):
        result = engine.rename(env_file, "DB_HOST", "DB_PORT")
        assert not result.success
        assert "already exists" in result.error

    def test_rename_to_same_name_is_allowed(self, env_file, engine):
        result = engine.rename(env_file, "DB_HOST", "DB_HOST")
        assert result.success
        assert env_file.get("DB_HOST") == "localhost"

    def test_audit_log_called_on_success(self, env_file):
        mock_audit = MagicMock()
        eng = RenameEngine(audit_log=mock_audit)
        eng.rename(env_file, "DB_HOST", "DATABASE_HOST")
        mock_audit.record.assert_called_once()
        call_kwargs = mock_audit.record.call_args.kwargs
        assert call_kwargs["action"] == "rename"
        assert call_kwargs["key"] == "DB_HOST"

    def test_audit_log_not_called_on_failure(self, env_file):
        mock_audit = MagicMock()
        eng = RenameEngine(audit_log=mock_audit)
        eng.rename(env_file, "NONEXISTENT", "NEW")
        mock_audit.record.assert_not_called()

    def test_rename_many_returns_all_results(self, env_file, engine):
        results = engine.rename_many(
            env_file, {"DB_HOST": "DATABASE_HOST", "DB_PORT": "DATABASE_PORT"}
        )
        assert len(results) == 2
        assert all(r.success for r in results)

    def test_rename_many_partial_failure_continues(self, env_file, engine):
        """rename_many should process all pairs even if some fail."""
        results = engine.rename_many(
            env_file, {"MISSING_KEY": "NEW_KEY", "DB_HOST": "DATABASE_HOST"}
        )
        assert len(results) == 2
        failures = [r for r in results if not r.success]
        successes = [r for r in results if r.success]
        assert len(failures) == 1
        assert failures[0].old_key == "MISSING_KEY"
        assert len(successes) == 1
        assert successes[0].old_key == "DB_HOST"
