"""
Tool execution module.

Handles the execution of tools with permission checking, hooks, and error handling.

Migrated from: services/tools/toolExecution.ts (1746 lines)
"""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ...core.tool import Tool


# Constants
HOOK_TIMING_DISPLAY_THRESHOLD_MS = 500
SLOW_PHASE_LOG_THRESHOLD_MS = 2000


@dataclass
class ToolExecutionResult:
    """Result of a tool execution."""

    success: bool = True
    output: Any = None
    error: str | None = None
    is_error: bool = False
    duration_ms: float = 0
    tool_use_id: str = ""
    tool_name: str = ""

    # Progress tracking
    progress_messages: list[dict[str, Any]] = field(default_factory=list)

    # Hook results
    pre_hook_results: list[dict[str, Any]] = field(default_factory=list)
    post_hook_results: list[dict[str, Any]] = field(default_factory=list)

    # Permission info
    permission_granted: bool = True
    permission_reason: str = ""


@dataclass
class ToolExecutionContext:
    """Context for tool execution."""

    tool_use_id: str
    tool_name: str
    input_data: dict[str, Any]
    session_id: str = ""
    request_id: str = ""
    agent_id: str = ""

    # Callbacks
    on_progress: Callable[[str], None] | None = None
    on_output: Callable[[Any], None] | None = None

    # Abort handling
    abort_signal: Any = None

    # Permission context
    cwd: str = ""
    allowed_paths: list[str] = field(default_factory=list)


def classify_tool_error(error: BaseException) -> str:
    """
    Classify a tool execution error into a telemetry-safe string.

    Extracts structured, telemetry-safe information:
    - TelemetrySafeError: use its telemetry_message (already vetted)
    - Node.js fs errors: log the error code (ENOENT, EACCES, etc.)
    - Known error types: use their name
    - Fallback: "Error"

    Args:
        error: The error to classify

    Returns:
        A telemetry-safe error classification string
    """
    from ...utils.errors import TelemetrySafeError, get_errno_code

    if isinstance(error, TelemetrySafeError):
        return error.telemetry_message[:200]

    if isinstance(error, Exception):
        # Check for errno code
        errno_code = get_errno_code(error)
        if errno_code:
            return f"Error:{errno_code}"

        # Check for stable name
        error_name = getattr(error, "name", error.__class__.__name__)
        if error_name and error_name != "Error" and len(error_name) > 3:
            return error_name[:60]

        return "Error"

    return "UnknownError"


async def execute_tool(
    tool: Tool,
    context: ToolExecutionContext,
) -> ToolExecutionResult:
    """
    Execute a tool with the given context.

    This is the core execution function that handles:
    - Input validation
    - Tool execution
    - Error handling
    - Progress reporting

    Args:
        tool: The tool to execute
        context: Execution context

    Returns:
        ToolExecutionResult with output or error
    """
    from ...utils.debug import log_for_debugging
    from ...utils.log import log_error

    start_time = time.time()
    result = ToolExecutionResult(
        tool_use_id=context.tool_use_id,
        tool_name=context.tool_name,
    )

    try:
        # Validate input
        validation_error = await tool.validate_input(context.input_data)
        if validation_error:
            result.success = False
            result.is_error = True
            result.error = validation_error
            return result

        # Execute the tool
        log_for_debugging(f"Executing tool: {context.tool_name}")

        output = await tool.call(
            context.input_data,
            context=context,
        )

        result.output = output
        result.success = True

    except Exception as e:
        log_error(e)
        result.success = False
        result.is_error = True
        result.error = str(e)

    finally:
        result.duration_ms = (time.time() - start_time) * 1000

    return result


async def execute_tool_with_hooks(
    tool: Tool,
    context: ToolExecutionContext,
    *,
    run_pre_hooks: bool = True,
    run_post_hooks: bool = True,
) -> ToolExecutionResult:
    """
    Execute a tool with pre and post hooks.

    This wraps the core execution with:
    - Pre-tool-use hooks
    - Permission checking
    - Post-tool-use hooks
    - Hook failure handling

    Args:
        tool: The tool to execute
        context: Execution context
        run_pre_hooks: Whether to run pre-tool-use hooks
        run_post_hooks: Whether to run post-tool-use hooks

    Returns:
        ToolExecutionResult with hook results
    """
    from ...hooks.tool_hooks import (
        execute_post_tool_use_hooks,
        execute_pre_tool_use_hooks,
    )
    from ...utils.debug import log_for_debugging

    result = ToolExecutionResult(
        tool_use_id=context.tool_use_id,
        tool_name=context.tool_name,
    )

    start_time = time.time()

    # Run pre-hooks
    if run_pre_hooks:
        pre_start = time.time()
        pre_results = await execute_pre_tool_use_hooks(
            tool_name=context.tool_name,
            tool_input=context.input_data,
            session_id=context.session_id,
        )
        pre_duration = (time.time() - pre_start) * 1000

        if pre_duration > SLOW_PHASE_LOG_THRESHOLD_MS:
            log_for_debugging(f"Slow pre-hooks for {context.tool_name}: {pre_duration:.0f}ms")

        result.pre_hook_results = pre_results

        # Check if any hook blocked execution
        for hook_result in pre_results:
            if hook_result.get("blocked"):
                result.success = False
                result.permission_granted = False
                result.permission_reason = hook_result.get("reason", "Blocked by hook")
                result.duration_ms = (time.time() - start_time) * 1000
                return result

    # Execute the tool
    exec_result = await execute_tool(tool, context)
    result.success = exec_result.success
    result.output = exec_result.output
    result.error = exec_result.error
    result.is_error = exec_result.is_error
    result.progress_messages = exec_result.progress_messages

    # Run post-hooks
    if run_post_hooks:
        post_start = time.time()
        post_results = await execute_post_tool_use_hooks(
            tool_name=context.tool_name,
            tool_input=context.input_data,
            tool_output=result.output,
            tool_error=result.error,
            session_id=context.session_id,
        )
        post_duration = (time.time() - post_start) * 1000

        if post_duration > SLOW_PHASE_LOG_THRESHOLD_MS:
            log_for_debugging(f"Slow post-hooks for {context.tool_name}: {post_duration:.0f}ms")

        result.post_hook_results = post_results

    result.duration_ms = (time.time() - start_time) * 1000
    return result


def format_tool_error(error: BaseException) -> str:
    """
    Format a tool error for display.

    Args:
        error: The error to format

    Returns:
        Formatted error string
    """
    from ...utils.errors import ShellError

    if isinstance(error, ShellError):
        parts = []
        if error.stderr:
            parts.append(f"stderr: {error.stderr}")
        if error.stdout:
            parts.append(f"stdout: {error.stdout}")
        parts.append(f"exit code: {error.code}")
        return "\n".join(parts)

    return str(error)


def is_permission_error(error: BaseException) -> bool:
    """Check if an error is a permission-related error."""
    from ...utils.errors import PermissionDeniedError, is_eacces

    if isinstance(error, PermissionDeniedError):
        return True

    return is_eacces(error)


def should_retry_tool(
    error: BaseException,
    attempt: int,
    max_attempts: int = 3,
) -> bool:
    """
    Determine if a tool execution should be retried.

    Args:
        error: The error that occurred
        attempt: Current attempt number (0-based)
        max_attempts: Maximum number of attempts

    Returns:
        True if the tool should be retried
    """
    if attempt >= max_attempts - 1:
        return False

    # Don't retry permission errors
    if is_permission_error(error):
        return False

    # Don't retry abort errors
    from ...utils.errors import is_abort_error

    if is_abort_error(error):
        return False

    # Retry transient errors
    error_str = str(error).lower()
    transient_patterns = [
        "timeout",
        "connection",
        "network",
        "temporary",
    ]

    return any(pattern in error_str for pattern in transient_patterns)
