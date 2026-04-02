"""
Environment utilities.

Functions for working with environment variables and config paths.

Migrated from: utils/envUtils.ts (184 lines)
"""

from __future__ import annotations

import os
import sys
from functools import cache


@cache
def get_claude_config_home_dir() -> str:
    """
    Get the Claude configuration home directory.

    Uses CLAUDE_CONFIG_DIR env var or defaults to ~/.claude
    """
    config_dir = os.getenv("CLAUDE_CONFIG_DIR")
    if config_dir:
        return os.path.normpath(config_dir)
    return os.path.expanduser("~/.claude")


def get_teams_dir() -> str:
    """Get the teams directory."""
    return os.path.join(get_claude_config_home_dir(), "teams")


def has_node_option(flag: str) -> bool:
    """
    Check if NODE_OPTIONS contains a specific flag.

    For Python, this checks sys.argv and relevant env vars.
    """
    # Not directly applicable to Python, but check sys.argv
    return flag in sys.argv


def is_env_truthy(env_var: str | bool | None) -> bool:
    """
    Check if an environment variable value is truthy.

    Returns True for: 1, true, yes, on (case insensitive)
    """
    if not env_var:
        return False
    if isinstance(env_var, bool):
        return env_var

    normalized = str(env_var).lower().strip()
    return normalized in ("1", "true", "yes", "on")


def is_env_defined_falsy(env_var: str | bool | None) -> bool:
    """
    Check if an environment variable is defined but falsy.

    Returns True for: 0, false, no, off (case insensitive)
    """
    if env_var is None:
        return False
    if isinstance(env_var, bool):
        return not env_var
    if not env_var:
        return False

    normalized = str(env_var).lower().strip()
    return normalized in ("0", "false", "no", "off")


def is_bare_mode() -> bool:
    """
    Check if running in bare mode.

    Bare mode skips hooks, LSP, plugin sync, skill dir-walk,
    attribution, background prefetches, and ALL keychain/credential reads.
    """
    if is_env_truthy(os.getenv("CLAUDE_CODE_SIMPLE")):
        return True
    return "--bare" in sys.argv


def parse_env_vars(raw_env_args: list[str] | None) -> dict[str, str]:
    """
    Parse an array of environment variable strings into a dict.

    Args:
        raw_env_args: List of strings in KEY=VALUE format

    Returns:
        Dict with key-value pairs

    Raises:
        ValueError: If format is invalid
    """
    parsed: dict[str, str] = {}

    if not raw_env_args:
        return parsed

    for env_str in raw_env_args:
        parts = env_str.split("=", 1)
        if len(parts) != 2 or not parts[0]:
            raise ValueError(
                f"Invalid environment variable format: {env_str}, "
                "environment variables should be added as: -e KEY1=value1 -e KEY2=value2"
            )
        parsed[parts[0]] = parts[1]

    return parsed


def get_aws_region() -> str:
    """
    Get the AWS region with fallback to default.

    Matches the Anthropic Bedrock SDK's region behavior.
    """
    return os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION") or "us-east-1"


def get_default_vertex_region() -> str:
    """Get the default Vertex AI region."""
    return os.getenv("CLOUD_ML_REGION") or "us-east5"


def should_maintain_project_working_dir() -> bool:
    """
    Check if bash commands should maintain project working directory.

    Returns true if CLAUDE_BASH_MAINTAIN_PROJECT_WORKING_DIR is set.
    """
    return is_env_truthy(os.getenv("CLAUDE_BASH_MAINTAIN_PROJECT_WORKING_DIR"))


def is_running_on_homespace() -> bool:
    """Check if running on Homespace (ant-internal cloud environment)."""
    return os.getenv("USER_TYPE") == "ant" and is_env_truthy(os.getenv("COO_RUNNING_ON_HOMESPACE"))


def is_in_protected_namespace() -> bool:
    """
    Check if running in a protected namespace.

    Conservative: assumes protected when signals are ambiguous.
    """
    # In Python version, we don't have the full namespace logic
    return os.getenv("USER_TYPE") == "ant"


def get_env_or_default(key: str, default: str = "") -> str:
    """Get an environment variable or return default."""
    return os.getenv(key, default)


def require_env(key: str) -> str:
    """
    Get a required environment variable.

    Raises ValueError if not set.
    """
    value = os.getenv(key)
    if value is None:
        raise ValueError(f"Required environment variable {key} is not set")
    return value
