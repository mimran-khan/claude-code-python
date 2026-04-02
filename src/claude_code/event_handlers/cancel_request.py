"""
Escape / Ctrl+C cancel priority and background-agent kill window.

Migrated from: hooks/useCancelRequest.ts (pure predicates + constants).
"""

from __future__ import annotations

from typing import Any

KILL_AGENTS_CONFIRM_WINDOW_MS = 3000


def vim_mode_enabled_stub() -> bool:
    """Replace with real vim-mode probe from settings (TS: isVimModeEnabled)."""
    return False


def cancel_escape_context_active(
    *,
    screen: str,
    is_searching_history: bool,
    is_message_selector_visible: bool,
    is_local_jsx_command: bool,
    is_help_open: bool,
    is_overlay_active: bool,
    vim_mode: str | None,
) -> bool:
    if screen == "transcript":
        return False
    if is_searching_history or is_message_selector_visible:
        return False
    if is_local_jsx_command or is_help_open or is_overlay_active:
        return False
    return not (vim_mode_enabled_stub() and vim_mode == "INSERT")


def cancel_escape_active(
    *,
    context_active: bool,
    can_cancel_running_task: bool,
    has_queued_commands: bool,
    input_mode: str | None,
    input_value: str | None,
    view_selection_mode: str,
) -> bool:
    is_in_special_mode_with_empty_input = input_mode is not None and input_mode != "prompt" and not (input_value or "")
    is_viewing_teammate = view_selection_mode == "viewing-agent"
    return bool(
        context_active
        and (can_cancel_running_task or has_queued_commands)
        and not is_in_special_mode_with_empty_input
        and not is_viewing_teammate
    )


def cancel_ctrl_c_active(
    *,
    context_active: bool,
    can_cancel_running_task: bool,
    has_queued_commands: bool,
    is_viewing_teammate: bool,
) -> bool:
    return bool(context_active and (can_cancel_running_task or has_queued_commands or is_viewing_teammate))


def parse_kill_agents_second_press(
    last_press_ms: float,
    now_ms: float,
) -> bool:
    """Return True if this press is the confirming second press inside the window."""
    return now_ms - last_press_ms <= KILL_AGENTS_CONFIRM_WINDOW_MS


def filter_tasks_running_local_agent(tasks: dict[str, Any]) -> list[tuple[str, Any]]:
    out: list[tuple[str, Any]] = []
    for tid, t in tasks.items():
        if t.get("type") == "local_agent" and t.get("status") == "running":
            out.append((tid, t))
    return out
