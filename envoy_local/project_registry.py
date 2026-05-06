"""Registry for tracking multiple projects and their .env file paths."""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional


DEFAULT_REGISTRY_PATH = Path.home() / ".envoy_local" / "registry.json"


class ProjectRegistry:
    """Manages a registry of project names mapped to their .env file paths."""

    def __init__(self, registry_path: Path = DEFAULT_REGISTRY_PATH):
        self.registry_path = Path(registry_path)
        self._projects: Dict[str, str] = {}
        self._load()

    def _load(self) -> None:
        """Load registry from disk if it exists."""
        if self.registry_path.exists():
            try:
                with open(self.registry_path, "r") as f:
                    self._projects = json.load(f)
            except (json.JSONDecodeError, OSError):
                self._projects = {}
        else:
            self._projects = {}

    def _save(self) -> None:
        """Persist registry to disk."""
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.registry_path, "w") as f:
            json.dump(self._projects, f, indent=2)

    def register(self, project_name: str, env_path: str) -> None:
        """Register a project with its .env file path."""
        env_path = str(Path(env_path).resolve())
        self._projects[project_name] = env_path
        self._save()

    def unregister(self, project_name: str) -> bool:
        """Remove a project from the registry. Returns True if removed."""
        if project_name in self._projects:
            del self._projects[project_name]
            self._save()
            return True
        return False

    def get_path(self, project_name: str) -> Optional[str]:
        """Return the .env path for a project, or None if not found."""
        return self._projects.get(project_name)

    def list_projects(self) -> List[str]:
        """Return sorted list of registered project names."""
        return sorted(self._projects.keys())

    def all_entries(self) -> Dict[str, str]:
        """Return a copy of all project -> path mappings."""
        return dict(self._projects)

    def __len__(self) -> int:
        return len(self._projects)

    def __contains__(self, project_name: str) -> bool:
        return project_name in self._projects
