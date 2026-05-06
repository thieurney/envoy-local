"""Tests for ProjectRegistry."""

import json
import pytest
from pathlib import Path

from envoy_local.project_registry import ProjectRegistry


@pytest.fixture
def registry(tmp_path):
    """Return a ProjectRegistry backed by a temporary directory."""
    registry_file = tmp_path / "registry.json"
    return ProjectRegistry(registry_path=registry_file)


@pytest.fixture
def sample_env(tmp_path):
    """Create a dummy .env file and return its path."""
    env_file = tmp_path / ".env"
    env_file.write_text("API_KEY=secret\n")
    return str(env_file)


class TestProjectRegistry:
    def test_empty_registry_on_init(self, registry):
        assert registry.list_projects() == []
        assert len(registry) == 0

    def test_register_project(self, registry, sample_env):
        registry.register("my_project", sample_env)
        assert "my_project" in registry
        assert registry.get_path("my_project") == str(Path(sample_env).resolve())

    def test_register_resolves_path(self, registry, tmp_path):
        relative = "."
        registry.register("proj", relative)
        stored = registry.get_path("proj")
        assert Path(stored).is_absolute()

    def test_list_projects_sorted(self, registry, sample_env):
        registry.register("zebra", sample_env)
        registry.register("alpha", sample_env)
        registry.register("middle", sample_env)
        assert registry.list_projects() == ["alpha", "middle", "zebra"]

    def test_unregister_existing_project(self, registry, sample_env):
        registry.register("to_remove", sample_env)
        result = registry.unregister("to_remove")
        assert result is True
        assert "to_remove" not in registry

    def test_unregister_nonexistent_returns_false(self, registry):
        result = registry.unregister("ghost")
        assert result is False

    def test_get_path_missing_returns_none(self, registry):
        assert registry.get_path("nonexistent") is None

    def test_all_entries(self, registry, sample_env):
        registry.register("proj_a", sample_env)
        registry.register("proj_b", sample_env)
        entries = registry.all_entries()
        assert set(entries.keys()) == {"proj_a", "proj_b"}

    def test_persistence_across_instances(self, tmp_path, sample_env):
        registry_file = tmp_path / "registry.json"
        r1 = ProjectRegistry(registry_path=registry_file)
        r1.register("persistent_proj", sample_env)

        r2 = ProjectRegistry(registry_path=registry_file)
        assert "persistent_proj" in r2
        assert r2.get_path("persistent_proj") == str(Path(sample_env).resolve())

    def test_corrupted_registry_file_resets_gracefully(self, tmp_path):
        registry_file = tmp_path / "registry.json"
        registry_file.write_text("not valid json{{{")
        registry = ProjectRegistry(registry_path=registry_file)
        assert registry.list_projects() == []

    def test_overwrite_existing_project(self, registry, tmp_path):
        env1 = str(tmp_path / ".env.old")
        env2 = str(tmp_path / ".env.new")
        Path(env1).write_text("A=1")
        Path(env2).write_text("B=2")
        registry.register("proj", env1)
        registry.register("proj", env2)
        assert registry.get_path("proj") == str(Path(env2).resolve())
        assert len(registry) == 1
