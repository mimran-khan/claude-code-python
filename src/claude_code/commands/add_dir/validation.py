"""
Validate directories before adding them as additional working directories.

Migrated from: commands/add-dir/validation.ts
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Literal

from claude_code.core.tool import ToolPermissionContext
from claude_code.utils.errors import get_errno_code
from claude_code.utils.path_utils import expand_path
from claude_code.utils.permissions.filesystem import path_in_working_path


@dataclass(frozen=True)
class AddDirectorySuccess:
    absolute_path: str
    result_type: Literal["success"] = "success"


@dataclass(frozen=True)
class AddDirectoryEmptyPath:
    result_type: Literal["empty_path"] = "empty_path"


@dataclass(frozen=True)
class AddDirectoryPathIssue:
    result_type: Literal["path_not_found", "not_a_directory"]
    directory_path: str
    absolute_path: str


@dataclass(frozen=True)
class AddDirectoryAlreadyCovered:
    directory_path: str
    working_dir: str
    result_type: Literal["already_in_working_directory"] = "already_in_working_directory"


AddDirectoryResult = AddDirectorySuccess | AddDirectoryEmptyPath | AddDirectoryPathIssue | AddDirectoryAlreadyCovered


def all_working_directories(
    permission_context: ToolPermissionContext,
    cwd: str | None = None,
) -> list[str]:
    """Primary cwd plus additional working directories from permission context."""
    base = os.path.abspath(cwd or os.getcwd())
    out: list[str] = [base]
    for entry in permission_context.additional_working_directories.values():
        out.append(os.path.abspath(expand_path(entry.path)))
    return out


async def validate_directory_for_workspace(
    directory_path: str,
    permission_context: ToolPermissionContext,
    cwd: str | None = None,
) -> AddDirectoryResult:
    if not directory_path:
        return AddDirectoryEmptyPath()

    absolute_path = os.path.abspath(expand_path(directory_path))

    try:
        is_dir = os.path.isdir(absolute_path)
        exists = os.path.exists(absolute_path) or os.path.islink(absolute_path)
    except OSError as e:
        code = get_errno_code(e)
        if code in ("ENOENT", "ENOTDIR", "EACCES", "EPERM"):
            return AddDirectoryPathIssue(
                result_type="path_not_found",
                directory_path=directory_path,
                absolute_path=absolute_path,
            )
        raise

    if not exists:
        return AddDirectoryPathIssue(
            result_type="path_not_found",
            directory_path=directory_path,
            absolute_path=absolute_path,
        )
    if not is_dir:
        return AddDirectoryPathIssue(
            result_type="not_a_directory",
            directory_path=directory_path,
            absolute_path=absolute_path,
        )

    current_working_dirs = all_working_directories(permission_context, cwd)
    for working_dir in current_working_dirs:
        if path_in_working_path(absolute_path, working_dir):
            return AddDirectoryAlreadyCovered(
                directory_path=directory_path,
                working_dir=working_dir,
            )

    return AddDirectorySuccess(absolute_path=absolute_path)


def add_dir_help_message(result: AddDirectoryResult) -> str:
    """User-facing explanation for validation outcome."""
    if isinstance(result, AddDirectoryEmptyPath):
        return "Please provide a directory path."
    if isinstance(result, AddDirectoryPathIssue):
        if result.result_type == "path_not_found":
            return f"Path {result.absolute_path} was not found."
        parent_dir = os.path.dirname(result.absolute_path)
        return f"{result.directory_path} is not a directory. Did you mean to add the parent directory {parent_dir}?"
    if isinstance(result, AddDirectoryAlreadyCovered):
        return (
            f"{result.directory_path} is already accessible within the existing working directory {result.working_dir}."
        )
    return f"Added {result.absolute_path} as a working directory."
