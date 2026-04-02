"""
User input processing.

Migrated from: utils/processUserInput/processUserInput.ts
"""

import shlex
import uuid as uuid_module
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from .process_text import process_text_prompt


@dataclass
class ProcessUserInputContext:
    """Context for processing user input."""

    cwd: str = ""
    session_id: str = ""
    permission_mode: str = "default"
    verbose: int = 0
    # Tool use context
    tools: dict[str, Any] = field(default_factory=dict)
    mcp_servers: dict[str, Any] = field(default_factory=dict)
    # Local JSX command context
    set_tool_jsx: Callable[..., None] | None = None
    clear_tool_jsx: Callable[..., None] | None = None


@dataclass
class ProcessUserInputBaseResult:
    """Result of processing user input."""

    messages: list[Any] = field(default_factory=list)
    should_query: bool = False
    allowed_tools: list[str] | None = None
    model: str | None = None
    effort: str | None = None
    result_text: str | None = None
    next_input: str | None = None
    submit_next_input: bool = False


async def process_user_input(
    input_text: str,
    context: ProcessUserInputContext,
    mode: str = "normal",
    pre_expansion_input: str | None = None,
    pasted_contents: list[Any] | None = None,
    ide_selection: Any | None = None,
    messages: list[Any] | None = None,
    set_user_input_on_processing: Callable | None = None,
    query_uuid: str | None = None,
    is_already_processing: bool = False,
    query_source: str | None = None,
    can_use_tool: Callable | None = None,
    skip_slash_commands: bool = False,
    bridge_origin: str | None = None,
) -> ProcessUserInputBaseResult:
    """Process user input and return messages for the conversation.

    This is the main entry point for processing user input. It handles:
    1. Slash command parsing and execution
    2. Attachment processing (images, files, etc.)
    3. Text prompt processing
    4. Hook execution

    Args:
        input_text: The raw user input
        context: Processing context
        mode: Input mode (normal, batch, etc.)
        pre_expansion_input: Input before any expansions
        pasted_contents: Any pasted content (images, etc.)
        ide_selection: Current IDE selection
        messages: Existing conversation messages
        set_user_input_on_processing: Callback when processing starts
        query_uuid: UUID for this query
        is_already_processing: If already processing a query
        query_source: Source of the query
        can_use_tool: Tool availability checker
        skip_slash_commands: Skip slash command processing
        bridge_origin: Origin for bridge commands

    Returns:
        ProcessUserInputBaseResult with messages and processing flags
    """
    query_uuid = query_uuid or str(uuid_module.uuid4())
    messages = messages or []
    pasted_contents = pasted_contents or []

    result = ProcessUserInputBaseResult()

    # Check for empty input
    if not input_text.strip() and not pasted_contents:
        return result

    # Check for slash commands
    if not skip_slash_commands and input_text.startswith("/"):
        command_result = await _process_slash_command(
            input_text,
            context,
            messages,
        )
        if command_result:
            return command_result

    # Process text prompt
    processed = await process_text_prompt(
        input_text,
        context,
        pasted_contents=pasted_contents,
        ide_selection=ide_selection,
    )

    if processed.get("messages"):
        result.messages = processed["messages"]
        result.should_query = True

    if processed.get("allowed_tools"):
        result.allowed_tools = processed["allowed_tools"]

    if processed.get("model"):
        result.model = processed["model"]

    return result


async def _process_slash_command(
    input_text: str,
    context: ProcessUserInputContext,
    messages: list[Any],
) -> ProcessUserInputBaseResult | None:
    """Process a slash command.

    Returns None if the command is unknown (fall through to normal prompt handling).
    """
    _ = messages
    parts = input_text[1:].split(maxsplit=1)
    if not parts:
        return None

    command_name = parts[0].lower()
    command_args = parts[1] if len(parts) > 1 else ""

    from ...commands import builtin as _builtin_commands  # noqa: F401
    from ...commands.base import CommandContext
    from ...commands.registry import get_command

    cmd = get_command(command_name)
    if cmd is None:
        return None

    try:
        arg_tokens = shlex.split(command_args, posix=True) if command_args.strip() else []
    except ValueError:
        out = ProcessUserInputBaseResult()
        out.result_text = f"Invalid quoting in /{command_name} arguments."
        return out

    cmd_ctx = CommandContext(cwd=context.cwd or ".", args=arg_tokens)
    exec_result = await cmd.execute(cmd_ctx)

    out = ProcessUserInputBaseResult()
    if exec_result.success:
        if isinstance(exec_result.output, str):
            out.result_text = exec_result.output
        elif exec_result.message:
            out.result_text = exec_result.message
        elif exec_result.output is not None:
            out.result_text = str(exec_result.output)
        else:
            out.result_text = ""
    else:
        out.result_text = exec_result.error or exec_result.message or "Command failed"

    return out


def create_user_message_from_input(
    input_text: str,
    attachments: list[Any] | None = None,
) -> dict[str, Any]:
    """Create a user message from input text and attachments."""
    content = []

    # Add text content
    if input_text:
        content.append(
            {
                "type": "text",
                "text": input_text,
            }
        )

    # Add attachment content
    if attachments:
        for attachment in attachments:
            if attachment.get("type") == "image":
                content.append(
                    {
                        "type": "image",
                        "source": attachment.get("source"),
                    }
                )
            elif attachment.get("type") == "file":
                # Convert file attachment to text
                content.append(
                    {
                        "type": "text",
                        "text": f"[File: {attachment.get('path')}]\n{attachment.get('content', '')}",
                    }
                )

    return {
        "type": "user",
        "id": str(uuid_module.uuid4()),
        "content": content,
    }
