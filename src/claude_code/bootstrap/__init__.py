"""
Bootstrap state management for Claude Code.

This module provides global state management for the application.
"""

from .state import (
    get_cwd_state,
    get_is_interactive,
    get_original_cwd,
    get_project_root,
    get_session_id,
    get_total_api_duration,
    get_total_cost_usd,
    get_total_duration,
    regenerate_session_id,
    reset_state_for_tests,
    set_cwd_state,
    set_is_interactive,
    set_original_cwd,
    set_project_root,
)

__all__ = [
    "get_session_id",
    "regenerate_session_id",
    "get_original_cwd",
    "get_project_root",
    "set_original_cwd",
    "set_project_root",
    "get_cwd_state",
    "set_cwd_state",
    "get_total_cost_usd",
    "get_total_api_duration",
    "get_total_duration",
    "get_is_interactive",
    "set_is_interactive",
    "reset_state_for_tests",
]
