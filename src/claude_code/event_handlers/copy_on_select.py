"""
Copy-on-select notification when terminal selection settles.

Migrated from: hooks/useCopyOnSelect.ts
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass


@dataclass
class SelectionStateLike:
    """Subset of Ink selection state."""

    is_dragging: bool = False


def maybe_copy_on_select_notification(
    *,
    selection_state: SelectionStateLike,
    has_selection: bool,
    get_copy_on_select_config_default_true: Callable[[], bool],
    copy_selection_no_clear: Callable[[], str],
    on_copied: Callable[[str], None] | None,
    copied_ref: list[bool],
) -> None:
    """
    Invoke after each selection mutation. ``copied_ref`` is a one-element box.

    Mirrors selection.subscribe callback body from useCopyOnSelect.
    """
    if selection_state.is_dragging:
        copied_ref[0] = False
        return
    if not has_selection:
        copied_ref[0] = False
        return
    if copied_ref[0]:
        return
    if not get_copy_on_select_config_default_true():
        return
    text = copy_selection_no_clear()
    if not text or not text.strip():
        copied_ref[0] = True
        return
    copied_ref[0] = True
    if on_copied is not None:
        on_copied(text)
