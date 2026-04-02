"""
Interactive / coordinator / swarm worker permission handlers.

Migrated from:
- hooks/toolPermission/handlers/interactiveHandler.ts
- hooks/toolPermission/handlers/coordinatorHandler.ts
- hooks/toolPermission/handlers/swarmWorkerHandler.ts

UI-heavy paths (confirm queue, bridge, channel relay) stay in the host; this
module exposes pure automation steps and constants the Python runtime can call.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Awaitable, Callable, Mapping
from typing import Any

from claude_code.tools.bash_tool.constants import BASH_TOOL_NAME

from .permission_context import ResolveOnce, create_resolve_once

logger = logging.getLogger(__name__)

# interactiveHandler.ts — ignore early keypresses on the permission dialog
PERMISSION_DIALOG_GRACE_PERIOD_MS = 200

__all__ = [
    "BASH_TOOL_NAME",
    "PERMISSION_DIALOG_GRACE_PERIOD_MS",
    "ResolveOnce",
    "create_resolve_once",
    "permission_prompt_within_grace_period",
    "run_coordinator_automated_permission_checks",
    "run_swarm_worker_classifier_gate",
]


def permission_prompt_within_grace_period(
    permission_prompt_start_time_ms: float,
    *,
    now_ms: float | None = None,
) -> bool:
    """True if the dialog is still inside the grace window (ignore interaction)."""
    now = now_ms if now_ms is not None else time.time() * 1000.0
    return (now - permission_prompt_start_time_ms) < PERMISSION_DIALOG_GRACE_PERIOD_MS


async def run_coordinator_automated_permission_checks(
    *,
    permission_mode: str | None,
    suggestions: list[Any] | None,
    updated_input: Mapping[str, Any] | None,
    run_hooks: Callable[
        [str | None, list[Any] | None, Mapping[str, Any] | None],
        Awaitable[Any | None],
    ],
    try_classifier: Callable[
        [Any | None, Mapping[str, Any] | None],
        Awaitable[Any | None],
    ]
    | None,
    pending_classifier_check: Any | None,
    bash_classifier_enabled: bool,
) -> Any | None:
    """
    Coordinator path: await hooks, then optional bash classifier.

    Returns a decision object if either step resolved the permission, or None
    to fall through to interactive handling (matches coordinatorHandler.ts).
    """
    try:
        hook_result = await run_hooks(permission_mode, suggestions, updated_input)
        if hook_result is not None:
            return hook_result

        if bash_classifier_enabled and try_classifier is not None:
            classifier_result = await try_classifier(pending_classifier_check, updated_input)
            if classifier_result is not None:
                return classifier_result
    except Exception:
        logger.exception("Automated permission check failed")
    return None


async def run_swarm_worker_classifier_gate(
    *,
    bash_classifier_enabled: bool,
    try_classifier: Callable[
        [Any | None, Mapping[str, Any] | None],
        Awaitable[Any | None],
    ]
    | None,
    pending_classifier_check: Any | None,
    updated_input: Mapping[str, Any] | None,
) -> Any | None:
    """
    Swarm worker path: classifier-only auto-approval before mailbox forward.

    Returns a decision when the classifier resolves; otherwise None so the
    caller can forward to the leader (matches swarmWorkerHandler.ts preamble).
    """
    if not bash_classifier_enabled or try_classifier is None:
        return None
    return await try_classifier(pending_classifier_check, updated_input)
