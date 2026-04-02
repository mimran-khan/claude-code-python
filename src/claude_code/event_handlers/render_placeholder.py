"""
Placeholder + inverse cursor rendering for prompt (non-React).

Migrated from: hooks/renderPlaceholder.ts (chalk replaced with plain strings / host styling).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass


@dataclass(frozen=True)
class PlaceholderRenderResult:
    rendered_placeholder: str | None
    show_placeholder: bool


def render_placeholder(
    *,
    placeholder: str | None,
    value: str,
    show_cursor: bool = False,
    focus: bool = False,
    terminal_focus: bool = True,
    invert: Callable[[str], str] | None = None,
    hide_placeholder_text: bool = False,
) -> PlaceholderRenderResult:
    """
    Return placeholder text and whether to show it (TS: renderPlaceholder).

    ``invert`` defaults to identity; host may wrap with ANSI inverse.
    """
    inv = invert or (lambda s: s)

    if not placeholder:
        return PlaceholderRenderResult(rendered_placeholder=None, show_placeholder=False)

    if hide_placeholder_text:
        text = inv(" ") if show_cursor and focus and terminal_focus else ""
        return PlaceholderRenderResult(rendered_placeholder=text, show_placeholder=bool(text))

    dimmed = placeholder
    if show_cursor and focus and terminal_focus:
        rendered = inv(placeholder[0]) + dimmed[1:] if placeholder else inv(" ")
    else:
        rendered = dimmed

    show_ph = len(value) == 0 and bool(placeholder)
    return PlaceholderRenderResult(rendered_placeholder=rendered, show_placeholder=show_ph)
