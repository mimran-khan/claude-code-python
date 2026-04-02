"""
Denial tracking for permission classifiers.

Tracks consecutive and total denials to determine when to fall back to prompting.

Migrated from: utils/permissions/denialTracking.ts (46 lines)
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class DenialTrackingState:
    """State for tracking permission denials."""

    consecutive_denials: int = 0
    total_denials: int = 0


@dataclass
class DenialLimits:
    """Limits for denial tracking."""

    max_consecutive: int = 3
    max_total: int = 20


DENIAL_LIMITS = DenialLimits()


def create_denial_tracking_state() -> DenialTrackingState:
    """Create a new denial tracking state."""
    return DenialTrackingState()


def record_denial(state: DenialTrackingState) -> DenialTrackingState:
    """Record a denial and return updated state."""
    return DenialTrackingState(
        consecutive_denials=state.consecutive_denials + 1,
        total_denials=state.total_denials + 1,
    )


def record_success(state: DenialTrackingState) -> DenialTrackingState:
    """Record a success (resets consecutive denials) and return updated state."""
    if state.consecutive_denials == 0:
        return state  # No change needed
    return DenialTrackingState(
        consecutive_denials=0,
        total_denials=state.total_denials,
    )


def should_fallback_to_prompting(state: DenialTrackingState) -> bool:
    """Check if we should fall back to prompting the user."""
    return state.consecutive_denials >= DENIAL_LIMITS.max_consecutive or state.total_denials >= DENIAL_LIMITS.max_total


def reset_denial_tracking() -> DenialTrackingState:
    """Reset denial tracking state."""
    return create_denial_tracking_state()


def get_denial_stats(state: DenialTrackingState) -> dict:
    """Get denial statistics."""
    return {
        "consecutive_denials": state.consecutive_denials,
        "total_denials": state.total_denials,
        "should_prompt": should_fallback_to_prompting(state),
    }
