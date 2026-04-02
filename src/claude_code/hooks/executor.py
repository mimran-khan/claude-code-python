"""
Hook executor.

Execute hooks and aggregate results.

Migrated from: utils/hooks/*.ts
"""

from __future__ import annotations

import asyncio
from typing import Any

import structlog

from .registry import RegisteredHook, get_hooks_for_event
from .types import (
    AggregatedHookResult,
    HookBlockingError,
    HookEvent,
    HookResult,
)

_LOG = structlog.get_logger(__name__)


async def execute_single_hook(
    hook: RegisteredHook,
    hook_input: dict[str, Any],
    tool_use_id: str | None = None,
    timeout: float | None = None,
) -> HookResult:
    """
    Execute a single hook.

    Args:
        hook: The hook to execute
        hook_input: Input data for the hook
        tool_use_id: Optional tool use ID
        timeout: Optional timeout override

    Returns:
        HookResult
    """
    effective_timeout = timeout or hook.timeout

    try:
        result = await asyncio.wait_for(
            hook.callback(hook_input, tool_use_id),
            timeout=effective_timeout,
        )

        return HookResult(
            outcome="success",
            additional_context=result.get("additionalContext"),
            updated_input=result.get("updatedInput"),
            permission_behavior=result.get("permissionDecision"),
            stop_reason=result.get("stopReason"),
            prevent_continuation=not result.get("continue", True),
        )

    except TimeoutError:
        return HookResult(
            outcome="non_blocking_error",
            blocking_error=HookBlockingError(
                blocking_error=f"Hook {hook.name} timed out after {effective_timeout}s",
                command=hook.name,
            ),
        )

    except asyncio.CancelledError:
        raise

    except Exception as e:
        _LOG.warning(
            "hook_callback_failed",
            hook_name=hook.name,
            error_type=type(e).__name__,
            error=str(e),
        )
        return HookResult(
            outcome="non_blocking_error",
            blocking_error=HookBlockingError(
                blocking_error=str(e),
                command=hook.name,
            ),
        )


async def execute_hooks(
    event: HookEvent,
    hook_input: dict[str, Any],
    tool_name: str | None = None,
    tool_use_id: str | None = None,
) -> AggregatedHookResult:
    """
    Execute all hooks for an event.

    Args:
        event: The hook event
        hook_input: Input data for hooks
        tool_name: Optional tool name for filtering
        tool_use_id: Optional tool use ID

    Returns:
        Aggregated results from all hooks
    """
    hooks = get_hooks_for_event(event, tool_name)

    if not hooks:
        return AggregatedHookResult()

    results = []
    for hook in hooks:
        result = await execute_single_hook(hook, hook_input, tool_use_id)
        results.append(result)

    return aggregate_hook_results(results)


def aggregate_hook_results(results: list[HookResult]) -> AggregatedHookResult:
    """
    Aggregate multiple hook results.

    Args:
        results: List of HookResult objects

    Returns:
        AggregatedHookResult
    """
    aggregated = AggregatedHookResult()

    for result in results:
        # Collect blocking errors
        if result.blocking_error:
            aggregated.blocking_errors.append(result.blocking_error)

        # Take first message
        if result.message and not aggregated.message:
            aggregated.message = result.message

        # Any prevention stops continuation
        if result.prevent_continuation:
            aggregated.prevent_continuation = True
            if result.stop_reason and not aggregated.stop_reason:
                aggregated.stop_reason = result.stop_reason

        # Collect additional contexts
        if result.additional_context:
            aggregated.additional_contexts.append(result.additional_context)

        # First non-passthrough permission behavior wins
        if (
            result.permission_behavior
            and result.permission_behavior != "passthrough"
            and not aggregated.permission_behavior
        ):
            aggregated.permission_behavior = result.permission_behavior
            aggregated.hook_permission_decision_reason = result.hook_permission_decision_reason

        # Take first initial user message
        if result.initial_user_message and not aggregated.initial_user_message:
            aggregated.initial_user_message = result.initial_user_message

        # Take first updated input
        if result.updated_input and not aggregated.updated_input:
            aggregated.updated_input = result.updated_input

        # Take first permission request result
        if result.permission_request_result and not aggregated.permission_request_result:
            aggregated.permission_request_result = result.permission_request_result

        # Any retry flag
        if result.retry:
            aggregated.retry = True

    return aggregated


async def execute_pre_tool_hooks(
    tool_name: str,
    tool_input: dict[str, Any],
    tool_use_id: str,
) -> AggregatedHookResult:
    """
    Execute pre-tool-use hooks.

    Args:
        tool_name: The tool being used
        tool_input: Input to the tool
        tool_use_id: The tool use ID

    Returns:
        Aggregated hook results
    """
    return await execute_hooks(
        event="PreToolUse",
        hook_input={
            "tool_name": tool_name,
            "tool_input": tool_input,
        },
        tool_name=tool_name,
        tool_use_id=tool_use_id,
    )


async def execute_post_tool_hooks(
    tool_name: str,
    tool_input: dict[str, Any],
    tool_output: Any,
    tool_use_id: str,
) -> AggregatedHookResult:
    """
    Execute post-tool-use hooks.

    Args:
        tool_name: The tool that was used
        tool_input: Input to the tool
        tool_output: Output from the tool
        tool_use_id: The tool use ID

    Returns:
        Aggregated hook results
    """
    return await execute_hooks(
        event="PostToolUse",
        hook_input={
            "tool_name": tool_name,
            "tool_input": tool_input,
            "tool_output": tool_output,
        },
        tool_name=tool_name,
        tool_use_id=tool_use_id,
    )
