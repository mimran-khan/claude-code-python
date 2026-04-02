"""
Auto Dream Configuration.

Configuration for background memory consolidation.
"""

from __future__ import annotations


def is_auto_dream_enabled() -> bool:
    """Check if background memory consolidation should run.

    User setting (autoDreamEnabled in settings.json) overrides the
    feature flag default when explicitly set.

    Returns:
        Whether auto dream is enabled
    """
    # In a full implementation, this would:
    # 1. Check user settings for explicit autoDreamEnabled value
    # 2. Fall back to feature flag / GrowthBook
    return False
