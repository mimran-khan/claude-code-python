"""
Configuration management for Claude Code.

This package provides configuration loading and management.
"""

from .config import (
    get_config_path,
    get_global_config,
    get_project_config,
    set_global_config,
)
from .types import (
    AccountInfo,
    GlobalConfig,
    HistoryEntry,
    PastedContent,
    ProjectConfig,
    ReleaseChannel,
)

__all__ = [
    "PastedContent",
    "HistoryEntry",
    "ProjectConfig",
    "GlobalConfig",
    "AccountInfo",
    "ReleaseChannel",
    "get_global_config",
    "get_project_config",
    "get_config_path",
    "set_global_config",
]
