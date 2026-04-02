"""
Suggestion utilities.

Command and directory completion suggestions.

Migrated from: utils/suggestions/*.ts (5 files)
"""

from .commands import (
    CommandSuggestion,
    get_command_suggestions,
    search_commands,
)
from .directory import (
    DirectorySuggestion,
    complete_path,
    get_directory_suggestions,
)
from .shell_history import (
    get_shell_history_suggestions,
    load_shell_history,
)
from .skill_usage import (
    get_frequently_used_skills,
    get_skill_usage_score,
    record_skill_usage,
)

__all__ = [
    # Commands
    "CommandSuggestion",
    "get_command_suggestions",
    "search_commands",
    # Directory
    "DirectorySuggestion",
    "get_directory_suggestions",
    "complete_path",
    # Shell history
    "get_shell_history_suggestions",
    "load_shell_history",
    # Skill usage
    "get_skill_usage_score",
    "record_skill_usage",
    "get_frequently_used_skills",
]
