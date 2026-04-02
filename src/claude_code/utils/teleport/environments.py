"""
Teleport environment management.

Migrated from: utils/teleport/environments.ts + environmentSelection.ts
"""

from dataclasses import dataclass


@dataclass
class Environment:
    """A remote execution environment."""

    id: str
    name: str
    description: str
    is_default: bool = False
    capabilities: list[str] = None

    def __post_init__(self):
        if self.capabilities is None:
            self.capabilities = []


# Default environments
DEFAULT_ENVIRONMENTS = [
    Environment(
        id="default",
        name="Default",
        description="Standard execution environment",
        is_default=True,
        capabilities=["python", "node", "shell"],
    ),
    Environment(
        id="python",
        name="Python",
        description="Python-focused environment",
        capabilities=["python", "pip", "shell"],
    ),
    Environment(
        id="node",
        name="Node.js",
        description="Node.js-focused environment",
        capabilities=["node", "npm", "shell"],
    ),
]


def get_available_environments() -> list[Environment]:
    """Get list of available environments."""
    return DEFAULT_ENVIRONMENTS.copy()


def get_default_environment() -> Environment:
    """Get the default environment."""
    for env in DEFAULT_ENVIRONMENTS:
        if env.is_default:
            return env
    return DEFAULT_ENVIRONMENTS[0]


def get_environment_by_id(env_id: str) -> Environment | None:
    """Get an environment by ID."""
    for env in DEFAULT_ENVIRONMENTS:
        if env.id == env_id:
            return env
    return None


def select_environment_for_task(task_description: str) -> Environment:
    """Select the best environment for a task based on description.

    This is a simple heuristic - in production would use more
    sophisticated matching.
    """
    task_lower = task_description.lower()

    if any(term in task_lower for term in ["python", "pip", "django", "flask"]):
        return get_environment_by_id("python") or get_default_environment()

    if any(term in task_lower for term in ["node", "npm", "javascript", "react", "typescript"]):
        return get_environment_by_id("node") or get_default_environment()

    return get_default_environment()
