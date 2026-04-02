"""
Filesystem permission utilities.

Functions for checking file and directory access permissions.

Migrated from: utils/permissions/filesystem.ts (1778 lines) - Core functionality
"""

from __future__ import annotations

import os
from typing import Any

from ..path_utils import expand_path

# Dangerous files that should be protected from auto-editing
DANGEROUS_FILES = [
    ".gitconfig",
    ".gitmodules",
    ".bashrc",
    ".bash_profile",
    ".zshrc",
    ".zprofile",
    ".profile",
    ".ripgreprc",
    ".mcp.json",
    ".claude.json",
]

# Dangerous directories that should be protected from auto-editing
DANGEROUS_DIRECTORIES = [
    ".git",
    ".vscode",
    ".idea",
    ".claude",
]


def normalize_case_for_comparison(path: str) -> str:
    """
    Normalize a path for case-insensitive comparison.

    This prevents bypassing security checks using mixed-case paths
    on case-insensitive filesystems (macOS/Windows).
    """
    return path.lower()


def is_claude_settings_path(file_path: str) -> bool:
    """Check if a path is a Claude settings file."""
    normalized = normalize_case_for_comparison(file_path)

    # Check for settings files
    settings_patterns = [
        ".claude/settings",
        ".claude.json",
        "settings.json",
        "settings.local.json",
    ]

    return any(pattern in normalized for pattern in settings_patterns)


def is_dangerous_file(file_path: str) -> bool:
    """
    Check if a file is in the dangerous files list.

    These files can be used for code execution or data exfiltration.
    """
    basename = os.path.basename(file_path)
    normalized = normalize_case_for_comparison(basename)

    return any(normalize_case_for_comparison(dangerous) == normalized for dangerous in DANGEROUS_FILES)


def is_dangerous_directory(dir_path: str) -> bool:
    """
    Check if a path is in or under a dangerous directory.

    These directories contain sensitive configuration or executable files.
    """
    normalized = normalize_case_for_comparison(dir_path)

    for dangerous in DANGEROUS_DIRECTORIES:
        dangerous_lower = normalize_case_for_comparison(dangerous)
        # Check if path contains this directory component
        if f"/{dangerous_lower}/" in normalized or normalized.endswith(f"/{dangerous_lower}"):
            return True
        if f"\\{dangerous_lower}\\" in normalized or normalized.endswith(f"\\{dangerous_lower}"):
            return True

    return False


def relative_path(from_path: str, to_path: str) -> str:
    """
    Cross-platform relative path calculation.

    Returns POSIX-style paths for consistency.
    """
    # Convert to absolute paths
    from_abs = os.path.abspath(from_path)
    to_abs = os.path.abspath(to_path)

    # Calculate relative path
    rel = os.path.relpath(to_abs, from_abs)

    # Convert to POSIX style
    return rel.replace("\\", "/")


def to_posix_path(path: str) -> str:
    """Convert a path to POSIX format."""
    return path.replace("\\", "/")


def path_in_working_path(
    file_path: str,
    cwd: str,
) -> bool:
    """
    Check if a file path is within the working directory.

    Args:
        file_path: The file path to check
        cwd: The current working directory

    Returns:
        True if the file is within cwd
    """
    try:
        abs_file = os.path.abspath(expand_path(file_path))
        abs_cwd = os.path.abspath(cwd)

        # Normalize for comparison
        abs_file_norm = normalize_case_for_comparison(abs_file)
        abs_cwd_norm = normalize_case_for_comparison(abs_cwd)

        # Check if file is within cwd
        return abs_file_norm.startswith(abs_cwd_norm + os.sep) or abs_file_norm == abs_cwd_norm
    except Exception:
        return False


def path_in_allowed_working_path(
    file_path: str,
    cwd: str,
    additional_paths: list[str] | None = None,
) -> bool:
    """
    Check if a file path is within the working directory or allowed paths.

    Args:
        file_path: The file path to check
        cwd: The current working directory
        additional_paths: Additional allowed paths

    Returns:
        True if the file is within cwd or additional paths
    """
    # First check cwd
    if path_in_working_path(file_path, cwd):
        return True

    # Check additional paths
    if additional_paths:
        for allowed_path in additional_paths:
            if path_in_working_path(file_path, allowed_path):
                return True

    return False


def matching_rule_for_input(
    tool_name: str,
    tool_input: dict[str, Any],
    rules: list[str],
    cwd: str,
) -> str | None:
    """
    Find a matching permission rule for a tool input.

    Args:
        tool_name: The name of the tool
        tool_input: The tool input dict
        rules: List of rule strings to check
        cwd: Current working directory

    Returns:
        The matching rule string if found, None otherwise
    """
    from .rule_parser import permission_rule_value_from_string

    for rule_string in rules:
        rule_value = permission_rule_value_from_string(rule_string)

        # Check if tool name matches
        if rule_value.tool_name != tool_name:
            continue

        # If no rule content, this is a tool-wide rule
        if not rule_value.rule_content:
            return rule_string

        # Check if rule content matches input
        if _rule_content_matches_input(rule_value.rule_content, tool_input, cwd):
            return rule_string

    return None


def _rule_content_matches_input(
    rule_content: str,
    tool_input: dict[str, Any],
    cwd: str,
) -> bool:
    """Check if a rule content pattern matches tool input."""
    # Get relevant input values
    input_values = []
    for key in ["command", "path", "file_path", "directory"]:
        if key in tool_input:
            input_values.append(str(tool_input[key]))

    if not input_values:
        return False

    # Check if any input value matches the rule content
    return any(_matches_pattern(value, rule_content, cwd) for value in input_values)


def _matches_pattern(value: str, pattern: str, cwd: str) -> bool:
    """Check if a value matches a gitignore-style pattern."""
    import fnmatch

    # Normalize paths
    value_normalized = to_posix_path(value)
    pattern_normalized = to_posix_path(pattern)

    # Try direct match
    if fnmatch.fnmatch(value_normalized, pattern_normalized):
        return True

    # Try relative path match
    try:
        rel_value = relative_path(cwd, value)
        if fnmatch.fnmatch(rel_value, pattern_normalized):
            return True
    except Exception:
        pass

    return False


def get_file_read_ignore_patterns() -> list[str]:
    """
    Get the default ignore patterns for file reading.

    These patterns prevent reading binary files and other
    non-text content.
    """
    return [
        "*.pyc",
        "*.pyo",
        "*.so",
        "*.dylib",
        "*.dll",
        "*.exe",
        "*.bin",
        "*.class",
        "*.jar",
        "*.war",
        "*.ear",
        "*.zip",
        "*.tar",
        "*.gz",
        "*.bz2",
        "*.7z",
        "*.rar",
        "*.png",
        "*.jpg",
        "*.jpeg",
        "*.gif",
        "*.bmp",
        "*.ico",
        "*.svg",
        "*.pdf",
        "*.doc",
        "*.docx",
        "*.xls",
        "*.xlsx",
        "*.ppt",
        "*.pptx",
        "*.mp3",
        "*.mp4",
        "*.wav",
        "*.avi",
        "*.mov",
        "*.mkv",
        "node_modules/**",
        ".git/**",
        "__pycache__/**",
        ".venv/**",
        "venv/**",
        ".env/**",
    ]


def normalize_patterns_to_path(
    patterns: list[str],
    base_path: str,
) -> list[str]:
    """
    Normalize pattern paths relative to a base path.

    Args:
        patterns: List of patterns to normalize
        base_path: Base path for relative patterns

    Returns:
        List of normalized absolute patterns
    """
    result = []

    for pattern in patterns:
        if os.path.isabs(pattern):
            result.append(pattern)
        else:
            result.append(os.path.join(base_path, pattern))

    return result


def get_claude_skill_scope(file_path: str) -> dict[str, str] | None:
    """
    If file_path is inside a .claude/skills/{name}/ directory,
    return the skill name and a session-allow pattern.

    Returns:
        Dict with 'skill_name' and 'pattern', or None if not a skill path
    """
    abs_path = os.path.abspath(expand_path(file_path))
    abs_path_lower = normalize_case_for_comparison(abs_path)

    # Check project skills dir
    from ..cwd import get_cwd

    cwd = get_cwd()
    project_skills = os.path.join(cwd, ".claude", "skills")

    # Check user skills dir
    home = os.path.expanduser("~")
    user_skills = os.path.join(home, ".claude", "skills")

    bases = [
        {"dir": project_skills, "prefix": "/.claude/skills/"},
        {"dir": user_skills, "prefix": "~/.claude/skills/"},
    ]

    for base in bases:
        dir_lower = normalize_case_for_comparison(base["dir"])

        # Check if path is under this skills directory
        if abs_path_lower.startswith(dir_lower + os.sep.lower()):
            # Extract skill name
            rest = abs_path[len(base["dir"]) + 1 :]

            # Find first separator
            sep_idx = rest.find("/")
            if sep_idx == -1:
                sep_idx = rest.find("\\")

            if sep_idx <= 0:
                return None

            skill_name = rest[:sep_idx]

            # Validate skill name
            if not skill_name or skill_name == "." or ".." in skill_name:
                return None

            # Reject glob metacharacters
            if any(c in skill_name for c in "*?[]"):
                return None

            return {
                "skill_name": skill_name,
                "pattern": f"{base['prefix']}{skill_name}/**",
            }

    return None
