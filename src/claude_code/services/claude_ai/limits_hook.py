"""
Subscribe to Claude.ai unified limit updates (TS: services/claudeAiLimitsHook.ts).

The TypeScript hook ``useClaudeAiLimits`` uses React state; in Python use
``claude_code.services.limits.tracker`` listeners instead. This module
documents parity and forwards to the tracker API.
"""

from __future__ import annotations

from claude_code.services.limits.tracker import (
    add_limits_listener,
    get_current_limits,
    remove_limits_listener,
)

__all__ = [
    "add_limits_listener",
    "remove_limits_listener",
    "get_current_limits",
]
