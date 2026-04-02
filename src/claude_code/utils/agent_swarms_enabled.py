"""
Runtime gate for agent teams / swarm (teammate) features.

Migrated from: utils/agentSwarmsEnabled.ts
"""

from __future__ import annotations

import os
import sys
from collections.abc import Callable
from typing import Any

SwarmFeatureGetter = Callable[[str, Any], Any]
_swarm_feature_getter: SwarmFeatureGetter | None = None


def set_swarm_feature_getter(getter: SwarmFeatureGetter | None) -> None:
    global _swarm_feature_getter
    _swarm_feature_getter = getter


def _env_truthy(val: str | None) -> bool:
    if val is None:
        return False
    return val.lower() in ("1", "true", "yes", "on")


def _is_agent_teams_flag_set() -> bool:
    return "--agent-teams" in sys.argv


def _growthbook_amber_flint_default_true() -> bool:
    if _swarm_feature_getter is None:
        return True
    return bool(_swarm_feature_getter("tengu_amber_flint", True))


def is_agent_swarms_enabled() -> bool:
    if os.environ.get("USER_TYPE") == "ant":
        return True
    opted_in = _env_truthy(os.environ.get("CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS")) or _is_agent_teams_flag_set()
    if not opted_in:
        return False
    return _growthbook_amber_flint_default_true()
