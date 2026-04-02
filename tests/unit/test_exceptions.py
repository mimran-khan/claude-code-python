"""Tests for claude_code.exceptions."""

from __future__ import annotations

from claude_code.exceptions import (
    ClaudeCodeError,
    OAuthFlowError,
    PluginLoadError,
    ToolExecutionError,
)


def test_exception_hierarchy() -> None:
    assert issubclass(PluginLoadError, ClaudeCodeError)
    assert issubclass(ToolExecutionError, ClaudeCodeError)
    assert issubclass(OAuthFlowError, ClaudeCodeError)


def test_chained_exception() -> None:
    cause = ValueError("root")
    try:
        raise PluginLoadError("mount failed") from cause
    except PluginLoadError as err:
        assert err.__cause__ is cause
