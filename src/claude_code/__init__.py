"""
Claude Code - Python implementation of the AI coding assistant.

This package provides the Python backend for Claude Code, including:
- Query engine for processing user prompts
- Tool system for file operations, shell commands, etc.
- MCP (Model Context Protocol) server for UI integration
- Services for API communication, context compaction, and permissions

Public attributes and submodules load on first access (PEP 562) so
``import claude_code`` stays lightweight.
"""

from __future__ import annotations

import importlib
from typing import Any

__version__ = "0.1.0"

_SUBMODULE_NAMES: frozenset[str] = frozenset(
    {
        "assistant",
        "buddy",
        "cli",
        "constants",
        "core",
        "entrypoints",
        "keybindings",
        "memdir",
        "migrations",
        "native",
        "query",
        "remote",
        "schemas",
        "server",
        "services",
        "skills",
        "state",
        "tools",
        "upstreamproxy",
        "utils",
        "voice",
    }
)

_EXPORT_SPECS: dict[str, tuple[str, str]] = {
    "ClaudeCodeError": ("claude_code.exceptions", "ClaudeCodeError"),
    "OAuthFlowError": ("claude_code.exceptions", "OAuthFlowError"),
    "PluginLoadError": ("claude_code.exceptions", "PluginLoadError"),
    "ToolExecutionError": ("claude_code.exceptions", "ToolExecutionError"),
    "get_session_id": ("claude_code.bootstrap", "get_session_id"),
    "Command": ("claude_code.commands", "Command"),
    "get_command": ("claude_code.commands", "get_command"),
    "QueryEngine": ("claude_code.engine", "QueryEngine"),
    "QueryEngineConfig": ("claude_code.engine", "QueryEngineConfig"),
    "HookEvent": ("claude_code.hooks", "HookEvent"),
    "HookResult": ("claude_code.hooks", "HookResult"),
    "execute_hooks": ("claude_code.hooks", "execute_hooks"),
    "register_hook": ("claude_code.hooks", "register_hook"),
    "Tool": ("claude_code.tools", "Tool"),
    "ToolResult": ("claude_code.tools", "ToolResult"),
    "AgentId": ("claude_code.types", "AgentId"),
    "AssistantMessage": ("claude_code.types", "AssistantMessage"),
    "Message": ("claude_code.types", "Message"),
    "SessionId": ("claude_code.types", "SessionId"),
    "UserMessage": ("claude_code.types", "UserMessage"),
}


def __getattr__(name: str) -> Any:
    if name in _SUBMODULE_NAMES:
        mod = importlib.import_module(f".{name}", __name__)
        globals()[name] = mod
        return mod
    if name in _EXPORT_SPECS:
        mod_path, attr = _EXPORT_SPECS[name]
        mod = importlib.import_module(mod_path)
        obj = getattr(mod, attr)
        globals()[name] = obj
        return obj
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)


def __dir__() -> list[str]:
    return sorted(__all__)


__all__ = [
    "__version__",
    "ClaudeCodeError",
    "OAuthFlowError",
    "PluginLoadError",
    "ToolExecutionError",
    "QueryEngine",
    "QueryEngineConfig",
    "Tool",
    "ToolResult",
    "SessionId",
    "AgentId",
    "Message",
    "UserMessage",
    "AssistantMessage",
    "get_session_id",
    "Command",
    "get_command",
    "HookEvent",
    "HookResult",
    "register_hook",
    "execute_hooks",
    "assistant",
    "constants",
    "core",
    "schemas",
    "services",
    "utils",
    "tools",
    "skills",
    "keybindings",
    "memdir",
    "cli",
    "entrypoints",
    "migrations",
    "state",
    "query",
    "server",
    "remote",
    "buddy",
    "upstreamproxy",
    "voice",
    "native",
]
