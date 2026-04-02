"""
Main query loop.

The core query loop that processes user prompts, calls the model,
executes tools, and manages the conversation state.

Migrated from: query.ts (1729 lines)
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator, Callable
from dataclasses import dataclass
from typing import (
    TYPE_CHECKING,
    Any,
)

from .config import build_query_config
from .deps import QueryDeps, production_deps
from .transitions import (
    Continue,
    ContinueNextTurn,
    Terminal,
    TerminalAbortedStreaming,
    TerminalAbortedTools,
    TerminalCompleted,
    TerminalHookStopped,
    TerminalMaxTurns,
    TerminalModelError,
)

if TYPE_CHECKING:
    from ..core.tool import ToolUseContext
    from ..types.message import (
        AssistantMessage,
        Message,
        StreamEvent,
        ToolUseSummaryMessage,
        UserMessage,
    )


MAX_OUTPUT_TOKENS_RECOVERY_LIMIT = 3


@dataclass
class AutoCompactTrackingState:
    """Tracking state for auto-compaction."""

    compacted: bool = False
    turn_id: str = ""
    turn_counter: int = 0
    consecutive_failures: int = 0


@dataclass
class QueryParams:
    """Parameters for the query function."""

    messages: list[Message]
    system_prompt: str
    user_context: dict[str, str]
    system_context: dict[str, str]
    can_use_tool: Callable[..., Any]
    tool_use_context: ToolUseContext
    fallback_model: str | None = None
    query_source: str = "repl_main_thread"
    max_output_tokens_override: int | None = None
    max_turns: int | None = None
    skip_cache_write: bool = False
    task_budget: dict[str, int] | None = None
    deps: QueryDeps | None = None


@dataclass
class QueryState:
    """Mutable state carried between loop iterations."""

    messages: list[Message]
    tool_use_context: ToolUseContext
    auto_compact_tracking: AutoCompactTrackingState | None = None
    max_output_tokens_recovery_count: int = 0
    has_attempted_reactive_compact: bool = False
    max_output_tokens_override: int | None = None
    pending_tool_use_summary: asyncio.Task | None = None
    stop_hook_active: bool | None = None
    turn_count: int = 1
    transition: Continue | None = None


async def query(
    params: QueryParams,
) -> AsyncGenerator[
    StreamEvent | Message | ToolUseSummaryMessage | Terminal,
    None,
]:
    """
    Main query function.

    Processes a conversation, calling the model, executing tools,
    and yielding messages as they are produced.

    Args:
        params: Query parameters

    Yields:
        Stream events, messages, tool use summaries, and terminal state
    """
    consumed_command_uuids: list[str] = []

    async for event in query_loop(params, consumed_command_uuids):
        yield event

    # Notify command lifecycle for consumed commands
    for uuid in consumed_command_uuids:
        _notify_command_lifecycle(uuid, "completed")


async def query_loop(
    params: QueryParams,
    consumed_command_uuids: list[str],
) -> AsyncGenerator[
    StreamEvent | Message | ToolUseSummaryMessage | Terminal,
    None,
]:
    """
    The main query loop.

    This is the core loop that:
    1. Prepares messages for the API
    2. Calls the model
    3. Processes tool uses
    4. Handles errors and recovery
    5. Continues until a terminal state
    """
    # Immutable params
    system_prompt = params.system_prompt
    user_context = params.user_context
    system_context = params.system_context
    can_use_tool = params.can_use_tool
    query_source = params.query_source
    max_turns = params.max_turns

    deps = params.deps or production_deps()

    # Mutable state
    state = QueryState(
        messages=params.messages,
        tool_use_context=params.tool_use_context,
        max_output_tokens_override=params.max_output_tokens_override,
    )

    # Build immutable config
    build_query_config()

    # Main loop
    while True:
        tool_use_context = state.tool_use_context
        messages = state.messages
        auto_compact_tracking = state.auto_compact_tracking
        pending_tool_use_summary = state.pending_tool_use_summary
        stop_hook_active = state.stop_hook_active
        turn_count = state.turn_count

        # Yield stream request start
        yield {"type": "stream_request_start"}

        # Initialize query tracking
        query_tracking = _get_or_create_query_tracking(tool_use_context, deps)

        tool_use_context = _update_tool_use_context(
            tool_use_context,
            query_tracking=query_tracking,
        )

        # Get messages for query (after compact boundary)
        messages_for_query = _get_messages_after_compact_boundary(messages)

        tracking = auto_compact_tracking

        # Apply microcompact
        microcompact_result = await deps.microcompact(
            messages_for_query,
            tool_use_context,
            query_source,
        )
        messages_for_query = microcompact_result.get("messages", messages_for_query)

        # Build full system prompt
        full_system_prompt = _append_system_context(system_prompt, system_context)

        # Apply autocompact
        autocompact_result = await deps.autocompact(
            messages_for_query,
            tool_use_context,
            {
                "system_prompt": system_prompt,
                "user_context": user_context,
                "system_context": system_context,
                "tool_use_context": tool_use_context,
                "fork_context_messages": messages_for_query,
            },
            query_source,
            tracking,
            0,  # snip_tokens_freed
        )

        compaction_result = autocompact_result.get("compaction_result")
        consecutive_failures = autocompact_result.get("consecutive_failures")

        if compaction_result:
            # Handle compaction result
            tracking = AutoCompactTrackingState(
                compacted=True,
                turn_id=deps.uuid(),
                turn_counter=0,
                consecutive_failures=0,
            )

            post_compact_messages = _build_post_compact_messages(compaction_result)
            for msg in post_compact_messages:
                yield msg

            messages_for_query = post_compact_messages
        elif consecutive_failures is not None:
            # Propagate failure count
            if tracking:
                tracking.consecutive_failures = consecutive_failures

        # Update tool use context with messages
        tool_use_context = _update_tool_use_context(
            tool_use_context,
            messages=messages_for_query,
        )

        # Track assistant messages and tool results
        assistant_messages: list[AssistantMessage] = []
        tool_results: list[UserMessage] = []
        tool_use_blocks: list[dict[str, Any]] = []
        needs_follow_up = False

        # Get current model
        tool_use_context.get_app_state()
        current_model = _get_runtime_main_loop_model(
            tool_use_context.options.get("main_loop_model", ""),
        )

        # Stream from model
        try:
            async for message in deps.call_model(
                messages=_prepend_user_context(messages_for_query, user_context),
                system_prompt=full_system_prompt,
                thinking_config=tool_use_context.options.get("thinking_config"),
                tools=tool_use_context.options.get("tools", []),
                signal=tool_use_context.abort_controller,
                model=current_model,
                query_source=query_source,
            ):
                yield message

                if message.get("type") == "assistant":
                    assistant_messages.append(message)

                    # Check for tool use blocks
                    content = message.get("message", {}).get("content", [])
                    for block in content:
                        if block.get("type") == "tool_use":
                            tool_use_blocks.append(block)
                            needs_follow_up = True

        except Exception as error:
            # Handle errors
            from ..utils.log import log_error

            log_error(error)

            # Yield error message
            yield _create_assistant_api_error_message(str(error))
            yield TerminalModelError(error=error)
            return

        # Check for abort during streaming
        if _is_aborted(tool_use_context):
            yield _create_user_interruption_message(tool_use=False)
            yield TerminalAbortedStreaming()
            return

        # Yield pending tool use summary
        if pending_tool_use_summary:
            try:
                summary = await pending_tool_use_summary
                if summary:
                    yield summary
            except Exception:
                pass

        # If no follow-up needed, we're done
        if not needs_follow_up:
            last_message = assistant_messages[-1] if assistant_messages else None

            # Check for API errors
            if last_message and last_message.get("is_api_error_message"):
                yield TerminalCompleted()
                return

            # TODO: Handle stop hooks

            yield TerminalCompleted()
            return

        # Execute tools
        updated_tool_use_context = tool_use_context
        should_prevent_continuation = False

        for tool_block in tool_use_blocks:
            # Execute each tool
            result = await _execute_tool(
                tool_block,
                assistant_messages,
                can_use_tool,
                tool_use_context,
            )

            if result.get("message"):
                yield result["message"]
                tool_results.append(result["message"])

            if result.get("new_context"):
                updated_tool_use_context = result["new_context"]

            if result.get("prevent_continuation"):
                should_prevent_continuation = True

        # Check for abort during tools
        if _is_aborted(tool_use_context):
            yield _create_user_interruption_message(tool_use=True)
            yield TerminalAbortedTools()
            return

        # If hook prevented continuation, stop
        if should_prevent_continuation:
            yield TerminalHookStopped()
            return

        # Update tracking
        if tracking and tracking.compacted:
            tracking.turn_counter += 1

        # Check max turns
        next_turn_count = turn_count + 1
        if max_turns and next_turn_count > max_turns:
            yield _create_attachment_message(
                {
                    "type": "max_turns_reached",
                    "max_turns": max_turns,
                    "turn_count": next_turn_count,
                }
            )
            yield TerminalMaxTurns(turn_count=next_turn_count)
            return

        # Continue to next iteration
        state = QueryState(
            messages=[*messages_for_query, *assistant_messages, *tool_results],
            tool_use_context=updated_tool_use_context,
            auto_compact_tracking=tracking,
            turn_count=next_turn_count,
            max_output_tokens_recovery_count=0,
            has_attempted_reactive_compact=False,
            pending_tool_use_summary=None,
            max_output_tokens_override=None,
            stop_hook_active=stop_hook_active,
            transition=ContinueNextTurn(),
        )


# Helper functions


def _get_or_create_query_tracking(
    tool_use_context: ToolUseContext,
    deps: QueryDeps,
) -> dict[str, Any]:
    """Get or create query tracking info."""
    existing = getattr(tool_use_context, "query_tracking", None)
    if existing:
        return {
            "chain_id": existing.get("chain_id", ""),
            "depth": existing.get("depth", 0) + 1,
        }
    return {
        "chain_id": deps.uuid(),
        "depth": 0,
    }


def _update_tool_use_context(
    context: ToolUseContext,
    **updates: Any,
) -> ToolUseContext:
    """Update tool use context with new values."""
    # Create a copy with updates
    result = context
    for key, value in updates.items():
        setattr(result, key, value)
    return result


def _get_messages_after_compact_boundary(
    messages: list[Message],
) -> list[Message]:
    """Get messages after the compact boundary."""
    # Find last compact boundary and return messages after it
    for i in range(len(messages) - 1, -1, -1):
        msg = messages[i]
        if msg.get("type") == "system" and msg.get("subtype") == "compact_boundary":
            return messages[i + 1 :]
    return messages


def _append_system_context(
    system_prompt: str,
    system_context: dict[str, str],
) -> str:
    """Append system context to the system prompt."""
    parts = [system_prompt]
    for key, value in system_context.items():
        if value:
            parts.append(f"\n\n<{key}>\n{value}\n</{key}>")
    return "".join(parts)


def _prepend_user_context(
    messages: list[Message],
    user_context: dict[str, str],
) -> list[Message]:
    """Prepend user context to messages."""
    if not user_context:
        return messages

    # Find first user message and prepend context
    result = list(messages)
    for i, msg in enumerate(result):
        if msg.get("type") == "user":
            context_parts = []
            for key, value in user_context.items():
                if value:
                    context_parts.append(f"<{key}>\n{value}\n</{key}>")

            if context_parts:
                original_content = msg.get("message", {}).get("content", "")
                if isinstance(original_content, str):
                    new_content = "\n\n".join(context_parts) + "\n\n" + original_content
                    result[i] = {
                        **msg,
                        "message": {**msg.get("message", {}), "content": new_content},
                    }
            break

    return result


def _build_post_compact_messages(
    compaction_result: dict[str, Any],
) -> list[Message]:
    """Build messages after compaction."""
    messages: list[Message] = []

    # Add summary messages
    for summary in compaction_result.get("summary_messages", []):
        messages.append(summary)

    # Add attachments
    for attachment in compaction_result.get("attachments", []):
        messages.append(attachment)

    # Add hook results
    for hook_result in compaction_result.get("hook_results", []):
        messages.append(hook_result)

    return messages


def _get_runtime_main_loop_model(main_loop_model: str) -> str:
    """Get the runtime main loop model."""
    import os

    return os.getenv("CLAUDE_CODE_MODEL", main_loop_model or "claude-sonnet-4-20250514")


def _is_aborted(tool_use_context: ToolUseContext) -> bool:
    """Check if the operation has been aborted."""
    controller = getattr(tool_use_context, "abort_controller", None)
    if controller:
        return getattr(controller, "aborted", False)
    return False


def _create_assistant_api_error_message(error: str) -> dict[str, Any]:
    """Create an assistant API error message."""
    return {
        "type": "assistant",
        "is_api_error_message": True,
        "message": {
            "role": "assistant",
            "content": error,
        },
    }


def _create_user_interruption_message(tool_use: bool) -> dict[str, Any]:
    """Create a user interruption message."""
    return {
        "type": "user",
        "message": {
            "role": "user",
            "content": "[Request interrupted by user]",
        },
        "is_interruption": True,
        "tool_use": tool_use,
    }


def _create_attachment_message(attachment: dict[str, Any]) -> dict[str, Any]:
    """Create an attachment message."""
    return {
        "type": "attachment",
        "attachment": attachment,
    }


async def _execute_tool(
    tool_block: dict[str, Any],
    assistant_messages: list[AssistantMessage],
    can_use_tool: Callable[..., Any],
    tool_use_context: ToolUseContext,
) -> dict[str, Any]:
    """Execute a single tool."""
    tool_name = tool_block.get("name", "")
    tool_input = tool_block.get("input", {})
    tool_use_id = tool_block.get("id", "")

    # Find the tool
    tools = tool_use_context.options.get("tools", [])
    tool = None
    for t in tools:
        if getattr(t, "name", "") == tool_name:
            tool = t
            break

    if not tool:
        return {
            "message": {
                "type": "user",
                "message": {
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": tool_use_id,
                            "content": f"Tool '{tool_name}' not found",
                            "is_error": True,
                        }
                    ],
                },
            },
        }

    # Check permissions
    can_use = await can_use_tool(tool_name, tool_input)
    if not can_use.get("allowed", True):
        return {
            "message": {
                "type": "user",
                "message": {
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": tool_use_id,
                            "content": can_use.get("reason", "Permission denied"),
                            "is_error": True,
                        }
                    ],
                },
            },
        }

    # Execute tool
    try:
        result = await tool.call(
            tool_input,
            tool_use_context,
            can_use_tool,
            assistant_messages[-1] if assistant_messages else None,
        )

        return {
            "message": {
                "type": "user",
                "message": {
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": tool_use_id,
                            "content": str(result.data) if hasattr(result, "data") else str(result),
                        }
                    ],
                },
            },
            "new_context": result.context_modifier(tool_use_context)
            if hasattr(result, "context_modifier") and result.context_modifier
            else None,
        }

    except Exception as e:
        return {
            "message": {
                "type": "user",
                "message": {
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": tool_use_id,
                            "content": f"Tool error: {str(e)}",
                            "is_error": True,
                        }
                    ],
                },
            },
        }


def _notify_command_lifecycle(uuid: str, state: str) -> None:
    """Notify about command lifecycle changes."""
    # Placeholder - actual implementation would notify listeners
    pass
