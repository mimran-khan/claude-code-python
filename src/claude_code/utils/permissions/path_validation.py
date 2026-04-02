"""
Path validation utilities for permissions.

Functions for validating file paths against permission rules.

Migrated from: utils/permissions/pathValidation.ts (486 lines) - Core logic
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Literal

from ..path_utils import expand_path
from ..platform import get_platform

MAX_DIRS_TO_LIST = 5
GLOB_PATTERN_REGEX = re.compile(r"[*?\[\]{}]")


FileOperationType = Literal["read", "write", "create"]


@dataclass
class PathCheckResult:
    """Result of a path permission check."""

    allowed: bool
    decision_reason: dict | None = None


@dataclass
class ResolvedPathCheckResult(PathCheckResult):
    """Path check result with resolved path."""

    resolved_path: str = ""


def format_directory_list(directories: list[str]) -> str:
    """Format a list of directories for display."""
    dir_count = len(directories)

    if dir_count <= MAX_DIRS_TO_LIST:
        return ", ".join(f"'{d}'" for d in directories)

    first_dirs = ", ".join(f"'{d}'" for d in directories[:MAX_DIRS_TO_LIST])
    return f"{first_dirs}, and {dir_count - MAX_DIRS_TO_LIST} more"


def get_glob_base_directory(path: str) -> str:
    """
    Extract the base directory from a glob pattern for validation.

    Example: "/path/to/*.txt" returns "/path/to"
    """
    match = GLOB_PATTERN_REGEX.search(path)
    if not match:
        return path

    # Get everything before the first glob character
    before_glob = path[: match.start()]

    # Find the last directory separator
    platform = get_platform()
    last_sep = max(before_glob.rfind("/"), before_glob.rfind("\\")) if platform == "windows" else before_glob.rfind("/")

    if last_sep == -1:
        return "."

    return before_glob[:last_sep] or "/"


def expand_tilde(path: str) -> str:
    """
    Expand tilde (~) at the start of a path to the user's home directory.

    Note: ~username expansion is not supported for security reasons.
    """
    if path == "~" or path.startswith("~/"):
        return os.path.expanduser("~") + path[1:]

    platform = get_platform()
    if platform == "windows" and path.startswith("~\\"):
        return os.path.expanduser("~") + path[1:]

    return path


def is_path_in_sandbox_write_allowlist(resolved_path: str) -> bool:
    """
    Check if a resolved path is writable according to the sandbox write allowlist.

    When the sandbox is enabled, the user has explicitly configured which
    directories are writable. We treat these as additional allowed write
    directories for path validation purposes.

    Note: This is a stub - sandbox functionality requires full implementation.
    """
    # Stub implementation - sandbox not implemented in Python version
    return False


def is_path_allowed(
    resolved_path: str,
    cwd: str,
    operation_type: FileOperationType,
    allow_rules: list[str] | None = None,
    deny_rules: list[str] | None = None,
    additional_paths: list[str] | None = None,
) -> PathCheckResult:
    """
    Check if a resolved path is allowed for the given operation type.

    Args:
        resolved_path: The resolved absolute path to check
        cwd: Current working directory
        operation_type: Type of operation (read, write, create)
        allow_rules: List of allow rule strings
        deny_rules: List of deny rule strings
        additional_paths: Additional allowed working directories

    Returns:
        PathCheckResult indicating if the operation is allowed
    """
    from .filesystem import (
        is_dangerous_directory,
        is_dangerous_file,
        path_in_allowed_working_path,
    )

    # 1. Check deny rules first
    if deny_rules:
        for rule in deny_rules:
            if _path_matches_rule(resolved_path, rule, cwd):
                return PathCheckResult(
                    allowed=False,
                    decision_reason={
                        "type": "rule",
                        "rule_string": rule,
                        "behavior": "deny",
                    },
                )

    # 2. For write/create operations, check safety validations
    if operation_type != "read":
        # Check for dangerous files
        if is_dangerous_file(resolved_path):
            return PathCheckResult(
                allowed=False,
                decision_reason={
                    "type": "safetyCheck",
                    "reason": f"Cannot auto-edit dangerous file: {os.path.basename(resolved_path)}",
                },
            )

        # Check for dangerous directories
        if is_dangerous_directory(resolved_path):
            return PathCheckResult(
                allowed=False,
                decision_reason={
                    "type": "safetyCheck",
                    "reason": "Cannot auto-edit files in dangerous directory",
                },
            )

    # 3. Check if path is in allowed working directory
    if path_in_allowed_working_path(resolved_path, cwd, additional_paths):
        return PathCheckResult(
            allowed=True,
            decision_reason={
                "type": "workingDir",
                "reason": "Path is within allowed working directory",
            },
        )

    # 4. Check allow rules
    if allow_rules:
        for rule in allow_rules:
            if _path_matches_rule(resolved_path, rule, cwd):
                return PathCheckResult(
                    allowed=True,
                    decision_reason={
                        "type": "rule",
                        "rule_string": rule,
                        "behavior": "allow",
                    },
                )

    # Default: not allowed
    return PathCheckResult(
        allowed=False,
        decision_reason={
            "type": "other",
            "reason": "Path is outside allowed working directories",
        },
    )


def _path_matches_rule(path: str, rule: str, cwd: str) -> bool:
    """Check if a path matches a permission rule."""
    import fnmatch

    # Expand the rule path
    rule_expanded = expand_path(rule, cwd)

    # Direct match
    if path == rule_expanded:
        return True

    # Glob pattern match
    if fnmatch.fnmatch(path, rule_expanded):
        return True

    # Directory prefix match
    if rule_expanded.endswith("/") or rule_expanded.endswith("**"):
        prefix = rule_expanded.rstrip("/*")
        if path.startswith(prefix):
            return True

    return False


def resolve_and_check_path(
    file_path: str,
    cwd: str,
    operation_type: FileOperationType,
    allow_rules: list[str] | None = None,
    deny_rules: list[str] | None = None,
    additional_paths: list[str] | None = None,
) -> ResolvedPathCheckResult:
    """
    Resolve a path and check if it's allowed.

    Args:
        file_path: The file path to check (may be relative)
        cwd: Current working directory
        operation_type: Type of operation
        allow_rules: List of allow rule strings
        deny_rules: List of deny rule strings
        additional_paths: Additional allowed working directories

    Returns:
        ResolvedPathCheckResult with resolved path and permission info
    """
    # Expand and resolve the path
    expanded = expand_tilde(file_path)
    if not os.path.isabs(expanded):
        expanded = os.path.join(cwd, expanded)
    resolved = os.path.normpath(expanded)

    # Check permissions
    result = is_path_allowed(
        resolved,
        cwd,
        operation_type,
        allow_rules,
        deny_rules,
        additional_paths,
    )

    return ResolvedPathCheckResult(
        allowed=result.allowed,
        decision_reason=result.decision_reason,
        resolved_path=resolved,
    )


def is_glob_pattern(path: str) -> bool:
    """Check if a path contains glob metacharacters."""
    return bool(GLOB_PATTERN_REGEX.search(path))


def validate_path_for_read(
    file_path: str,
    cwd: str,
    additional_paths: list[str] | None = None,
) -> ResolvedPathCheckResult:
    """Validate a path for read operations."""
    return resolve_and_check_path(
        file_path,
        cwd,
        "read",
        additional_paths=additional_paths,
    )


def validate_path_for_write(
    file_path: str,
    cwd: str,
    allow_rules: list[str] | None = None,
    deny_rules: list[str] | None = None,
    additional_paths: list[str] | None = None,
) -> ResolvedPathCheckResult:
    """Validate a path for write operations."""
    return resolve_and_check_path(
        file_path,
        cwd,
        "write",
        allow_rules,
        deny_rules,
        additional_paths,
    )


def validate_path_for_create(
    file_path: str,
    cwd: str,
    allow_rules: list[str] | None = None,
    deny_rules: list[str] | None = None,
    additional_paths: list[str] | None = None,
) -> ResolvedPathCheckResult:
    """Validate a path for create operations."""
    return resolve_and_check_path(
        file_path,
        cwd,
        "create",
        allow_rules,
        deny_rules,
        additional_paths,
    )
