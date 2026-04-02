"""Tips service for showing helpful tips to users."""

from .history import (
    get_sessions_since_last_shown,
    get_tip_history,
    record_tip_shown,
)
from .registry import (
    Tip,
    TipContext,
    get_all_tips,
    get_tip_by_id,
    register_tip,
)
from .scheduler import (
    get_next_tip,
    mark_tip_shown,
    should_show_tip,
)

__all__ = [
    "Tip",
    "TipContext",
    "get_all_tips",
    "get_tip_by_id",
    "register_tip",
    "should_show_tip",
    "get_next_tip",
    "mark_tip_shown",
    "get_tip_history",
    "get_sessions_since_last_shown",
    "record_tip_shown",
]
