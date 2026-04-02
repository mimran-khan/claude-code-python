"""
Whether /model, /fast, /effort should run during an active query turn.

Migrated from: utils/immediateCommand.ts
"""

from __future__ import annotations

import os


def should_inference_config_command_be_immediate() -> bool:
    """
    Always True for internal ``ant`` users; otherwise GrowthBook flag
    ``tengu_immediate_model_command``.
    """
    if os.environ.get("USER_TYPE") == "ant":
        return True
    try:
        from claude_code.services.analytics.growthbook import get_feature_value_cached
    except ImportError:
        return False
    return bool(get_feature_value_cached("tengu_immediate_model_command", False))
