"""
Ctrl+R history search — async iteration over prompt history.

Migrated from: hooks/useHistorySearch.ts
"""

from __future__ import annotations

import asyncio
import importlib.util
import sys
from collections.abc import AsyncIterator, Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

# Real submodule name so history.py's relative imports (e.g. ``.bootstrap``) resolve.
_PROMPT_HISTORY_MODULE = "claude_code._prompt_history_file"


def _load_prompt_history_module() -> object:
    """Load sibling ``history.py`` (prompt log) — not the ``history/`` package."""
    path = Path(__file__).resolve().parents[1] / "history.py"
    spec = importlib.util.spec_from_file_location(_PROMPT_HISTORY_MODULE, path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Cannot load claude_code/history.py for prompt history reader")
    mod = importlib.util.module_from_spec(spec)
    mod.__package__ = "claude_code"
    sys.modules[_PROMPT_HISTORY_MODULE] = mod
    spec.loader.exec_module(mod)
    return mod


_ph = _load_prompt_history_module()
HistoryEntry = _ph.HistoryEntry
make_history_reader = _ph.make_history_reader

PromptInputMode = Literal["prompt", "bash", "plan"]


def get_mode_from_input(display: str) -> PromptInputMode:
    """Infer mode prefix from stored display string (TS getModeFromInput parity)."""
    if display.startswith("!"):
        return "bash"
    if display.startswith("#"):
        return "plan"
    return "prompt"


def get_value_from_input(display: str) -> str:
    """Strip mode prefix for cursor positioning."""
    if display.startswith("!") or display.startswith("#"):
        return display[1:]
    return display


async def close_history_reader(reader: AsyncIterator[HistoryEntry] | None) -> None:
    """Close async generator / iterator to release file handles (TS .return())."""
    if reader is None:
        return
    aclose = getattr(reader, "aclose", None)
    if callable(aclose):
        await aclose()


@dataclass
class HistorySearchMutableState:
    """Holds mutable session state equivalent to React useState/useRef."""

    is_searching: bool = False
    history_query: str = ""
    history_failed_match: bool = False
    original_input: str = ""
    original_cursor_offset: int = 0
    original_mode: PromptInputMode = "prompt"
    original_pasted: dict[int, object] = field(default_factory=dict)
    history_match: HistoryEntry | None = None
    reader: AsyncIterator[HistoryEntry] | None = None
    seen_prompts: set[str] = field(default_factory=set)


def start_history_search(
    state: HistorySearchMutableState,
    *,
    current_input: str,
    current_cursor: int,
    current_mode: PromptInputMode,
    current_pasted: dict[int, object],
) -> None:
    state.is_searching = True
    state.original_input = current_input
    state.original_cursor_offset = current_cursor
    state.original_mode = current_mode
    state.original_pasted = dict(current_pasted)
    state.seen_prompts.clear()
    state.reader = make_history_reader()


def handle_history_backspace_when_empty(
    state: HistorySearchMutableState,
    *,
    key: str,
    on_restore_originals: Callable[[], None] | None = None,
) -> bool:
    """
    Cancel search when backspace fires with an empty query (TS useHistorySearch parity).

    When ``on_restore_originals`` is provided, it runs before async reset (input/cursor/paste).
    """
    if not state.is_searching or key != "backspace" or state.history_query != "":
        return False
    if on_restore_originals is not None:
        on_restore_originals()
    asyncio.get_running_loop().create_task(reset_history_search(state))
    return True


async def search_history(
    state: HistorySearchMutableState,
    *,
    resume: bool,
    cancel_event: asyncio.Event | None = None,
    apply_match: Callable[[str, PromptInputMode, int, dict[int, object]], None] | None = None,
    apply_restore_originals: Callable[[], None] | None = None,
) -> None:
    """
    Advance history match for current query.

    When ``history_query`` is empty, calls ``apply_restore_originals`` if provided.

    When a match is found, calls ``apply_match(display, mode, cursor_offset, pasted)``.
    """
    if not state.is_searching:
        return

    if state.history_query == "":
        await close_history_reader(state.reader)
        state.reader = None
        state.seen_prompts.clear()
        state.history_match = None
        state.history_failed_match = False
        if apply_restore_originals is not None:
            apply_restore_originals()
        return

    if not resume:
        await close_history_reader(state.reader)
        state.reader = make_history_reader()
        state.seen_prompts.clear()

    reader = state.reader
    if reader is None:
        return

    while True:
        if cancel_event is not None and cancel_event.is_set():
            return
        try:
            item = await reader.__anext__()
        except StopAsyncIteration:
            state.history_failed_match = True
            return

        display = item.display
        pos = display.rfind(state.history_query)
        if pos != -1 and display not in state.seen_prompts:
            state.seen_prompts.add(display)
            state.history_match = item
            state.history_failed_match = False
            mode = get_mode_from_input(display)
            value = get_value_from_input(display)
            clean_pos = value.rfind(state.history_query)
            cursor = clean_pos if clean_pos != -1 else pos
            if apply_match is not None:
                apply_match(display, mode, cursor, dict(item.pasted_contents))
            return


async def reset_history_search(state: HistorySearchMutableState) -> None:
    """Clear search UI state and close reader (TS reset())."""
    state.is_searching = False
    state.history_query = ""
    state.history_failed_match = False
    state.original_input = ""
    state.original_cursor_offset = 0
    state.original_mode = "prompt"
    state.original_pasted = {}
    state.history_match = None
    await close_history_reader(state.reader)
    state.reader = None
    state.seen_prompts.clear()


async def accept_history_match(
    state: HistorySearchMutableState,
    *,
    set_input: Callable[[str], None],
    set_mode: Callable[[PromptInputMode], None],
    set_pasted: Callable[[dict[int, object]], None],
) -> None:
    """historySearch:accept — apply match (or restore originals) then reset."""
    if state.history_match:
        set_mode(get_mode_from_input(state.history_match.display))
        set_input(get_value_from_input(state.history_match.display))
        set_pasted(dict(state.history_match.pasted_contents))
    else:
        set_pasted(dict(state.original_pasted))
    await reset_history_search(state)


async def cancel_history_search(
    state: HistorySearchMutableState,
    *,
    set_input: Callable[[str], None],
    set_cursor: Callable[[int], None],
    set_pasted: Callable[[dict[int, object]], None],
) -> None:
    """historySearch:cancel — restore prompt before search."""
    set_input(state.original_input)
    set_cursor(state.original_cursor_offset)
    set_pasted(dict(state.original_pasted))
    await reset_history_search(state)


async def execute_history_search(
    state: HistorySearchMutableState,
    *,
    on_accept_history: Callable[[HistoryEntry], None],
    set_mode: Callable[[PromptInputMode], None],
) -> None:
    """historySearch:execute — submit original or matched entry."""
    if state.history_query == "":
        on_accept_history(
            HistoryEntry(display=state.original_input, pasted_contents=dict(state.original_pasted)),
        )
    elif state.history_match:
        set_mode(get_mode_from_input(state.history_match.display))
        on_accept_history(
            HistoryEntry(
                display=get_value_from_input(state.history_match.display),
                pasted_contents=dict(state.history_match.pasted_contents),
            ),
        )
    await reset_history_search(state)
