"""
Domain-specific exceptions for Claude Code.

Use these for clear error boundaries and ``raise ... from err`` chaining.
"""

from __future__ import annotations


class ClaudeCodeError(Exception):
    """Base exception for recoverable Claude Code failures."""


class PluginLoadError(ClaudeCodeError):
    """Raised when a plugin cannot be loaded, mounted, or activated."""


class ToolExecutionError(ClaudeCodeError):
    """Raised when a built-in tool fails in a way callers should surface."""


class OAuthFlowError(ClaudeCodeError):
    """Raised when the OAuth authorization flow fails before tokens are issued."""


__all__ = [
    "ClaudeCodeError",
    "OAuthFlowError",
    "PluginLoadError",
    "ToolExecutionError",
]
