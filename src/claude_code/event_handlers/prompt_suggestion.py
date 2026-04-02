"""
Prompt speculation telemetry + accept/ignore bookkeeping.

Migrated from: hooks/usePromptSuggestion.ts
"""

from __future__ import annotations

import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any


@dataclass
class PromptSuggestionState:
    text: str | None
    prompt_id: str | None
    shown_at: float
    accepted_at: float
    generation_request_id: str | None


def visible_suggestion(
    state: PromptSuggestionState,
    *,
    is_assistant_responding: bool,
    input_value: str,
) -> str | None:
    if is_assistant_responding or len(input_value) > 0:
        return None
    return state.text


def log_prompt_suggestion_outcome(
    *,
    state: PromptSuggestionState,
    final_input: str,
    log_event: Callable[[str, Mapping[str, Any]], None],
    tab_was_pressed: bool,
) -> None:
    st = state.text or ""
    shown = state.shown_at
    accepted = tab_was_pressed or final_input == st
    now_ms = time.time() * 1000
    log_event(
        "tengu_prompt_suggestion",
        {
            "outcome": "accepted" if accepted else "ignored",
            "prompt_id": state.prompt_id,
            "timeToAcceptMs": (state.accepted_at or 0) - shown if accepted else None,
            "timeToIgnoreMs": None if accepted else now_ms - shown,
        },
    )
