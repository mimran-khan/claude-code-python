"""
Ultraplan keyword detection and session management.

Migrated from: utils/ultraplan/*.ts
"""

from .ccr_session import (
    ULTRAPLAN_TELEPORT_SENTINEL,
    ExitPlanModeScanner,
    PollResult,
    UltraplanPollError,
    poll_for_approved_exit_plan_mode,
)
from .keyword import (
    TriggerPosition,
    find_ultraplan_trigger_positions,
    find_ultrareview_trigger_positions,
    has_ultraplan_keyword,
    has_ultrareview_keyword,
    replace_ultraplan_keyword,
)

__all__ = [
    "TriggerPosition",
    "find_ultraplan_trigger_positions",
    "find_ultrareview_trigger_positions",
    "has_ultraplan_keyword",
    "has_ultrareview_keyword",
    "replace_ultraplan_keyword",
    "ULTRAPLAN_TELEPORT_SENTINEL",
    "ExitPlanModeScanner",
    "PollResult",
    "UltraplanPollError",
    "poll_for_approved_exit_plan_mode",
]
