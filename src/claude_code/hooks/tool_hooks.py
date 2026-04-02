"""
Tool-specific hooks.

Hooks for tool execution lifecycle events.

Migrated from: services/tools/toolHooks.ts
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .executor import execute_hooks
from .types import HookInput, HookResult

if TYPE_CHECKING:
    from ..types.message import Message


async def execute_pre_tool_use_hooks(
    tool_name: str,
    tool_input: dict[str, Any],
    tool_use_context: Any,
    messages: list[Message] | None = None,
) -> HookResult:
    """
    Execute pre-tool-use hooks.

    Called before a tool is executed. Hooks can:
    - Modify the tool input
    - Prevent tool execution
    - Log/audit tool usage

    Args:
        tool_name: Name of the tool
        tool_input: Tool input parameters
        tool_use_context: Tool use context
        messages: Current messages

    Returns:
        Hook result
    """
    input_data = HookInput(
        event="PreToolUse",
        session_id=getattr(tool_use_context, "session_id", ""),
        tool_name=tool_name,
        tool_input=tool_input,
        messages=messages or [],
        context={
            "tool_use_context": tool_use_context,
        },
    )

    return await execute_hooks("PreToolUse", input_data)


async def execute_post_tool_use_hooks(
    tool_name: str,
    tool_input: dict[str, Any],
    tool_output: str,
    tool_use_context: Any,
    messages: list[Message] | None = None,
) -> HookResult:
    """
    Execute post-tool-use hooks.

    Called after a tool has executed. Hooks can:
    - Modify the tool output
    - Log/audit tool results
    - Trigger follow-up actions

    Args:
        tool_name: Name of the tool
        tool_input: Tool input parameters
        tool_output: Tool output
        tool_use_context: Tool use context
        messages: Current messages

    Returns:
        Hook result
    """
    input_data = HookInput(
        event="PostToolUse",
        session_id=getattr(tool_use_context, "session_id", ""),
        tool_name=tool_name,
        tool_input=tool_input,
        tool_output=tool_output,
        messages=messages or [],
        context={
            "tool_use_context": tool_use_context,
        },
    )

    return await execute_hooks("PostToolUse", input_data)


async def execute_pre_sampling_hooks(
    messages: list[Message],
    system_prompt: str,
    user_context: dict[str, str],
    system_context: dict[str, str],
    tool_use_context: Any,
    query_source: str = "",
) -> HookResult:
    """
    Execute pre-sampling hooks.

    Called before sending messages to the model. Hooks can:
    - Modify messages or context
    - Add additional context
    - Prevent sampling

    Args:
        messages: Messages to send
        system_prompt: System prompt
        user_context: User context
        system_context: System context
        tool_use_context: Tool use context
        query_source: Query source

    Returns:
        Hook result
    """
    input_data = HookInput(
        event="PreSampling",
        session_id=getattr(tool_use_context, "session_id", ""),
        messages=messages,
        context={
            "system_prompt": system_prompt,
            "user_context": user_context,
            "system_context": system_context,
            "tool_use_context": tool_use_context,
            "query_source": query_source,
        },
    )

    return await execute_hooks("PreSampling", input_data)


async def execute_post_sampling_hooks(
    messages: list[Message],
    system_prompt: str,
    user_context: dict[str, str],
    system_context: dict[str, str],
    tool_use_context: Any,
    query_source: str = "",
) -> HookResult:
    """
    Execute post-sampling hooks.

    Called after receiving a response from the model. Hooks can:
    - Process or log the response
    - Trigger follow-up actions

    Args:
        messages: Messages including response
        system_prompt: System prompt
        user_context: User context
        system_context: System context
        tool_use_context: Tool use context
        query_source: Query source

    Returns:
        Hook result
    """
    input_data = HookInput(
        event="PostSampling",
        session_id=getattr(tool_use_context, "session_id", ""),
        messages=messages,
        context={
            "system_prompt": system_prompt,
            "user_context": user_context,
            "system_context": system_context,
            "tool_use_context": tool_use_context,
            "query_source": query_source,
        },
    )

    return await execute_hooks("PostSampling", input_data)


async def execute_stop_hooks(
    messages: list[Message],
    assistant_messages: list[Message],
    tool_use_context: Any,
    stop_hook_active: bool | None = None,
) -> dict[str, Any]:
    """
    Execute stop hooks.

    Called when the model indicates it wants to stop. Hooks can:
    - Evaluate if the stop is appropriate
    - Request continuation
    - Add blocking errors

    Args:
        messages: All messages
        assistant_messages: Assistant messages this turn
        tool_use_context: Tool use context
        stop_hook_active: Whether stop hooks are currently active

    Returns:
        Result with prevent_continuation and blocking_errors
    """
    input_data = HookInput(
        event="Stop",
        session_id=getattr(tool_use_context, "session_id", ""),
        messages=messages,
        context={
            "assistant_messages": assistant_messages,
            "tool_use_context": tool_use_context,
            "stop_hook_active": stop_hook_active,
        },
    )

    result = await execute_hooks("Stop", input_data)

    return {
        "prevent_continuation": not result.allowed,
        "blocking_errors": result.blocking_errors,
    }


async def execute_stop_failure_hooks(
    last_message: Message | None,
    tool_use_context: Any,
) -> None:
    """
    Execute stop failure hooks.

    Called when stopping due to an error. Hooks can:
    - Log the failure
    - Clean up resources

    Args:
        last_message: The last message (usually an error)
        tool_use_context: Tool use context
    """
    input_data = HookInput(
        event="StopFailure",
        session_id=getattr(tool_use_context, "session_id", ""),
        messages=[last_message] if last_message else [],
        context={
            "tool_use_context": tool_use_context,
        },
    )

    await execute_hooks("StopFailure", input_data)


async def execute_pre_compact_hooks(
    messages: list[Message],
    tool_use_context: Any,
) -> HookResult:
    """
    Execute pre-compaction hooks.

    Called before compacting conversation history.

    Args:
        messages: Messages to compact
        tool_use_context: Tool use context

    Returns:
        Hook result
    """
    input_data = HookInput(
        event="PreCompact",
        session_id=getattr(tool_use_context, "session_id", ""),
        messages=messages,
        context={
            "tool_use_context": tool_use_context,
        },
    )

    return await execute_hooks("PreCompact", input_data)


async def execute_post_compact_hooks(
    messages: list[Message],
    tool_use_context: Any,
) -> HookResult:
    """
    Execute post-compaction hooks.

    Called after compacting conversation history.

    Args:
        messages: Compacted messages
        tool_use_context: Tool use context

    Returns:
        Hook result
    """
    input_data = HookInput(
        event="PostCompact",
        session_id=getattr(tool_use_context, "session_id", ""),
        messages=messages,
        context={
            "tool_use_context": tool_use_context,
        },
    )

    return await execute_hooks("PostCompact", input_data)
