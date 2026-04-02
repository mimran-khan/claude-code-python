"""
Hook utilities.

Event hooks for tool execution, API queries, and file changes.

Migrated from: utils/hooks/*.ts (17 files)
"""

from .async_hook_registry import AsyncHookRegistry
from .config import (
    HookConfig,
    HookMatcher,
    get_hooks_for_event,
    load_hooks_config,
)
from .events import (
    HookEventHandler,
    HookExecutionEvent,
    HookProgressEvent,
    HookResponseEvent,
    HookStartedEvent,
    emit_hook_progress,
    emit_hook_response,
    emit_hook_started,
    enable_all_hook_events,
    register_hook_event_handler,
)
from .exec_prompt_hook import PromptHookResult, exec_prompt_hook
from .helpers import (
    HookResponse,
    add_arguments_to_prompt,
    validate_hook_response,
)
from .post_sampling_hooks import (
    PostSamplingContext,
    clear_post_sampling_hooks,
    register_post_sampling_hook,
    run_post_sampling_hooks,
)
from .session import (
    SessionHook,
    SessionHookRegistry,
    add_session_hook,
    clear_session_hooks,
    get_session_hooks,
    remove_session_hook,
)
from .ssrf_guard import SsrfCheckResult, is_url_hook_safe

__all__ = [
    # Events
    "HookStartedEvent",
    "HookProgressEvent",
    "HookResponseEvent",
    "HookExecutionEvent",
    "HookEventHandler",
    "register_hook_event_handler",
    "emit_hook_started",
    "emit_hook_progress",
    "emit_hook_response",
    "enable_all_hook_events",
    # Helpers
    "add_arguments_to_prompt",
    "HookResponse",
    "validate_hook_response",
    # Session
    "SessionHook",
    "SessionHookRegistry",
    "add_session_hook",
    "remove_session_hook",
    "get_session_hooks",
    "clear_session_hooks",
    # Config
    "HookConfig",
    "HookMatcher",
    "load_hooks_config",
    "get_hooks_for_event",
    # Batch-3 hook modules
    "AsyncHookRegistry",
    "PromptHookResult",
    "exec_prompt_hook",
    "PostSamplingContext",
    "register_post_sampling_hook",
    "run_post_sampling_hooks",
    "clear_post_sampling_hooks",
    "SsrfCheckResult",
    "is_url_hook_safe",
]
