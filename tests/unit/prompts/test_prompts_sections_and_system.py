"""Unit tests for ``claude_code.prompts`` (sections + system prompt assembly)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from claude_code.prompts import (
    DEFAULT_AGENT_PROMPT,
    SYSTEM_PROMPT_DYNAMIC_BOUNDARY,
    get_env_info,
    get_system_prompt,
)
from claude_code.prompts.sections import (
    get_actions_section,
    get_doing_tasks_section,
    get_intro_section,
    get_output_efficiency_section,
    get_system_section,
    get_tone_and_style_section,
    get_using_tools_section,
    prepend_bullets,
)


def test_prepend_bullets_mixed_strings_and_nested_lists() -> None:
    out = prepend_bullets(["a", ["b", "c"], "d"])
    assert " - a" in out
    assert "  - b" in out
    assert "  - c" in out
    assert " - d" in out


def test_section_helpers_return_non_empty_markdown() -> None:
    assert "IMPORTANT" in get_intro_section()
    assert "# System" in get_system_section()
    assert "# Doing tasks" in get_doing_tasks_section()
    assert "# Executing actions" in get_actions_section()
    assert "# Tone and style" in get_tone_and_style_section()
    assert "# Output efficiency" in get_output_efficiency_section()


def test_get_using_tools_section_includes_todo_when_enabled() -> None:
    base = get_using_tools_section(set())
    with_todo = get_using_tools_section({"TodoWrite"})
    assert "TodoWrite" not in base
    assert "TodoWrite" in with_todo


def test_get_system_prompt_contains_boundary_and_env() -> None:
    tools = [MagicMock(spec=["name"], name="Read"), MagicMock(spec=["name"], name="Grep")]

    with (
        patch("claude_code.prompts.system.get_cwd", return_value="/tmp/proj"),
        patch("claude_code.prompts.system._is_git_repo", return_value=False),
        patch("claude_code.prompts.system.platform.system", return_value="Darwin"),
        patch("claude_code.prompts.system.platform.release", return_value="24.0"),
    ):
        parts = get_system_prompt(tools, "claude-3-opus", additional_working_directories=["/other"])

    joined = "\n".join(parts)
    assert SYSTEM_PROMPT_DYNAMIC_BOUNDARY in parts
    assert "/tmp/proj" in joined
    assert "/other" in joined
    assert "claude-3-opus" in joined


def test_get_env_info_windows_uname_branch() -> None:
    with (
        patch("claude_code.prompts.system.get_cwd", return_value="C:\\\\repo"),
        patch("claude_code.prompts.system._is_git_repo", return_value=True),
        patch("claude_code.prompts.system.platform.system", return_value="Windows"),
        patch("claude_code.prompts.system.platform.release", return_value="11"),
        patch("claude_code.prompts.system.platform.version", return_value="Win10Pro"),
    ):
        text = get_env_info("model-x")

    assert "Primary working directory: C:\\\\repo" in text
    assert "Win10Pro" in text


def test_default_agent_prompt_is_non_empty() -> None:
    assert "Claude Code" in DEFAULT_AGENT_PROMPT
