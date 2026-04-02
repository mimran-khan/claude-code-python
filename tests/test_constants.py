"""Tests for migrated tool and settings constant modules."""

from __future__ import annotations

import pytest

from claude_code.tools.bash_tool.constants import BASH_TOOL_NAME
from claude_code.tools.file_read_tool.constants import (
    DESCRIPTION as FILE_READ_DESCRIPTION,
    FILE_READ_TOOL_NAME,
    FILE_UNCHANGED_STUB,
    MAX_LINES_TO_READ,
)
from claude_code.tools.file_write_tool.constants import DESCRIPTION as FILE_WRITE_DESCRIPTION
from claude_code.tools.file_write_tool.constants import FILE_WRITE_TOOL_NAME
from claude_code.tools.glob_tool.constants import DESCRIPTION as GLOB_DESCRIPTION
from claude_code.tools.glob_tool.constants import GLOB_TOOL_NAME
from claude_code.tools.grep_tool.constants import GREP_TOOL_NAME


def test_bash_tool_name_constant() -> None:
    assert BASH_TOOL_NAME == "Bash"
    assert isinstance(BASH_TOOL_NAME, str)


def test_file_read_constants() -> None:
    assert FILE_READ_TOOL_NAME == "Read"
    assert "filesystem" in FILE_READ_DESCRIPTION.lower()
    assert isinstance(FILE_UNCHANGED_STUB, str) and len(FILE_UNCHANGED_STUB) > 20
    assert isinstance(MAX_LINES_TO_READ, int) and MAX_LINES_TO_READ > 0


def test_file_write_constants() -> None:
    assert FILE_WRITE_TOOL_NAME == "Write"
    assert isinstance(FILE_WRITE_DESCRIPTION, str)


def test_glob_constants() -> None:
    assert GLOB_TOOL_NAME == "Glob"
    assert isinstance(GLOB_DESCRIPTION, str)


def test_grep_tool_name_constant() -> None:
    assert GREP_TOOL_NAME == "Grep"


@pytest.mark.parametrize(
    "module_path,expected_names",
    [
        ("claude_code.tools.bash_tool.constants", ["BASH_TOOL_NAME"]),
        ("claude_code.tools.file_read_tool.constants", ["FILE_READ_TOOL_NAME", "DESCRIPTION"]),
    ],
)
def test_constant_modules_export_expected_symbols(module_path: str, expected_names: list[str]) -> None:
    mod = __import__(module_path, fromlist=["*"])
    for name in expected_names:
        assert hasattr(mod, name), f"{module_path} missing {name}"
