"""
Hooks system.

Event hooks for extending Claude Code behavior.

Migrated from: hooks/*.ts + utils/hooks/*.ts + types/hooks.ts
"""

# Permission hooks
from . import permission
from .executor import (
    execute_hooks,
    execute_post_tool_hooks,
    execute_pre_tool_hooks,
)
from .registry import (
    HookRegistry,
    get_hooks_for_event,
    register_hook,
    unregister_hook,
)
from .types import (
    HOOK_EVENTS,
    HookBlockingError,
    HookCallbackContext,
    HookEvent,
    HookProgress,
    HookResult,
    is_async_hook_output,
    is_hook_event,
    is_sync_hook_output,
)

__all__ = [
    # Types
    "HookEvent",
    "HOOK_EVENTS",
    "HookResult",
    "HookProgress",
    "HookBlockingError",
    "HookCallbackContext",
    "is_hook_event",
    "is_sync_hook_output",
    "is_async_hook_output",
    # Registry
    "HookRegistry",
    "register_hook",
    "unregister_hook",
    "get_hooks_for_event",
    # Executor
    "execute_hooks",
    "execute_pre_tool_hooks",
    "execute_post_tool_hooks",
    # Permission submodule
    "permission",
]
