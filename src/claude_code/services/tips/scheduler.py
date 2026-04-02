"""Tip scheduler for determining when to show tips."""

import random

from .history import get_sessions_since_last_shown, get_show_count
from .registry import Tip, TipContext, get_all_tips

MIN_SESSIONS_BETWEEN_TIPS = 3


def should_show_tip(context: TipContext | None = None) -> bool:
    """Check if we should show a tip this session."""
    sessions = get_sessions_since_last_shown(None)
    return sessions >= MIN_SESSIONS_BETWEEN_TIPS


def get_next_tip(context: TipContext | None = None) -> Tip | None:
    """Get the next tip to show."""
    if not should_show_tip(context):
        return None

    context = context or TipContext()
    eligible_tips = []

    for tip in get_all_tips():
        # Check max shows
        if get_show_count(tip.id) >= tip.max_shows:
            continue

        # Check condition
        if tip.condition and not tip.condition(context):
            continue

        eligible_tips.append(tip)

    if not eligible_tips:
        return None

    # Sort by priority (higher first)
    eligible_tips.sort(key=lambda t: -t.priority)

    # Return highest priority, with some randomization among equal priorities
    top_priority = eligible_tips[0].priority
    top_tips = [t for t in eligible_tips if t.priority == top_priority]

    return random.choice(top_tips)


def mark_tip_shown(tip_id: str) -> None:
    """Mark a tip as shown."""
    from .history import record_tip_shown

    record_tip_shown(tip_id)
