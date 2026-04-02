"""Unit tests for ``claude_code.schemas.hook_schemas``."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from claude_code.schemas.hook_schemas import (
    AgentHook,
    BashCommandHook,
    HookMatcher,
    HttpHook,
    PromptHook,
    parse_hook_command,
    parse_hooks_settings,
)


def test_bash_command_hook_accepts_allowed_shell() -> None:
    h = BashCommandHook(command="echo hi", shell="bash")
    assert h.type == "command"
    assert h.shell == "bash"


def test_bash_command_hook_rejects_unknown_shell() -> None:
    with pytest.raises(ValidationError, match="shell"):
        BashCommandHook(command="x", shell="zsh")  # type: ignore[arg-type]


def test_bash_command_hook_timeout_must_be_positive() -> None:
    with pytest.raises(ValidationError):
        BashCommandHook(command="x", timeout=0)


def test_prompt_http_agent_discriminated_models() -> None:
    p = PromptHook(prompt="check")
    assert p.type == "prompt"
    http = HttpHook(url="https://example.com/hook")
    assert http.type == "http"
    ag = AgentHook(prompt="go")
    assert ag.type == "agent"


def test_parse_hook_command_dispatches_by_type() -> None:
    cmd = parse_hook_command({"type": "command", "command": "ls"})
    assert isinstance(cmd, BashCommandHook)
    pr = parse_hook_command({"type": "prompt", "prompt": "hi"})
    assert isinstance(pr, PromptHook)


def test_parse_hooks_settings_filters_unknown_events_and_non_lists() -> None:
    raw = {
        "SessionStart": [
            {"matcher": None, "hooks": [{"type": "command", "command": "date"}]},
        ],
        "NotARealEvent": [],
        "PreToolUse": "should-be-list",
    }
    settings = parse_hooks_settings(raw)
    assert "NotARealEvent" not in settings
    assert "PreToolUse" not in settings
    assert len(settings["SessionStart"]) == 1
    assert isinstance(settings["SessionStart"][0], HookMatcher)


def test_hook_matcher_extra_fields_forbidden() -> None:
    with pytest.raises(ValidationError):
        HookMatcher.model_validate({"matcher": "x", "hooks": [], "extra": 1})
