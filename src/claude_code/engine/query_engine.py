"""
QueryEngine - core query lifecycle and session state management.

This module owns the query lifecycle and session state for a conversation.
It extracts the core logic from ask() into a standalone class that can be
used by both the headless/SDK path and the REPL.

One QueryEngine per conversation. Each submitMessage() call starts a new
turn within the same conversation. State (messages, file cache, usage, etc.)
persists across turns.

Migrated from: QueryEngine.ts (1295 lines)
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator, Callable
from dataclasses import dataclass, field
from typing import (
    TYPE_CHECKING,
    Any,
    Literal,
)

if TYPE_CHECKING:
    from ..commands.registry import Command
    from ..core.tool import ToolPermissionContext, Tools
    from ..types.message import Message


@dataclass
class NonNullableUsage:
    """Token usage statistics."""

    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_input_tokens: int = 0
    cache_creation_input_tokens: int = 0


EMPTY_USAGE = NonNullableUsage()


@dataclass
class SDKPermissionDenial:
    """Record of a permission denial for SDK reporting."""

    tool_name: str
    tool_use_id: str
    tool_input: dict[str, Any]


@dataclass
class ThinkingConfig:
    """Configuration for thinking mode."""

    type: Literal["disabled", "adaptive", "enabled"] = "disabled"
    budget_tokens: int | None = None


@dataclass
class FileStateCache:
    """Cache for file read state."""

    entries: dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentDefinition:
    """Definition of an agent."""

    name: str
    type: str
    description: str = ""


@dataclass
class AgentDefinitionsResult:
    """Result of loading agent definitions."""

    active_agents: list[AgentDefinition] = field(default_factory=list)
    all_agents: list[AgentDefinition] = field(default_factory=list)
    allowed_agent_types: list[str] | None = None


@dataclass
class AppState:
    """Application state."""

    tool_permission_context: ToolPermissionContext
    file_history: dict[str, Any] = field(default_factory=dict)
    attribution: dict[str, Any] = field(default_factory=dict)
    fast_mode: bool = False
    mcp: dict[str, Any] = field(default_factory=lambda: {"tools": [], "clients": []})
    effort_value: str | None = None
    advisor_model: str | None = None


@dataclass
class OrphanedPermission:
    """An orphaned permission from a previous session."""

    tool_use_id: str
    tool_name: str
    tool_input: dict[str, Any]


@dataclass
class QueryEngineConfig:
    """Configuration for QueryEngine."""

    cwd: str
    tools: Tools
    commands: list[Command]
    mcp_clients: list[Any]
    agents: list[AgentDefinition]
    can_use_tool: Callable[..., Any]
    get_app_state: Callable[[], AppState]
    set_app_state: Callable[[Callable[[AppState], AppState]], None]
    initial_messages: list[Message] | None = None
    read_file_cache: FileStateCache | None = None
    custom_system_prompt: str | None = None
    append_system_prompt: str | None = None
    user_specified_model: str | None = None
    fallback_model: str | None = None
    thinking_config: ThinkingConfig | None = None
    max_turns: int | None = None
    max_budget_usd: float | None = None
    task_budget: dict[str, int] | None = None
    json_schema: dict[str, Any] | None = None
    verbose: bool = False
    replay_user_messages: bool = False
    handle_elicitation: Callable[..., Any] | None = None
    include_partial_messages: bool = False
    set_sdk_status: Callable[[Any], None] | None = None
    abort_controller: Any | None = None
    orphaned_permission: OrphanedPermission | None = None
    snip_replay: Callable[..., Any] | None = None


@dataclass
class SDKMessage:
    """Base SDK message type."""

    type: str = ""
    session_id: str = ""
    uuid: str = ""


@dataclass
class SDKResultMessage:
    """Result message from SDK."""

    type: str = "result"
    subtype: str = "success"
    session_id: str = ""
    uuid: str = ""
    is_error: bool = False
    duration_ms: int = 0
    duration_api_ms: int = 0
    num_turns: int = 0
    result: str = ""
    stop_reason: str | None = None
    total_cost_usd: float = 0.0
    usage: NonNullableUsage = field(default_factory=lambda: EMPTY_USAGE)
    model_usage: dict[str, Any] = field(default_factory=dict)
    permission_denials: list[SDKPermissionDenial] = field(default_factory=list)
    fast_mode_state: dict[str, Any] | None = None
    structured_output: Any = None
    errors: list[str] | None = None


class QueryEngine:
    """
    QueryEngine owns the query lifecycle and session state for a conversation.

    One QueryEngine per conversation. Each submit_message() call starts a new
    turn within the same conversation. State (messages, file cache, usage, etc.)
    persists across turns.
    """

    def __init__(self, config: QueryEngineConfig) -> None:
        self.config = config
        self._mutable_messages: list[Message] = list(config.initial_messages or [])
        self._abort_controller = config.abort_controller or _create_abort_controller()
        self._permission_denials: list[SDKPermissionDenial] = []
        self._total_usage = NonNullableUsage()
        self._has_handled_orphaned_permission = False
        self._read_file_state = config.read_file_cache or FileStateCache()
        self._discovered_skill_names: set[str] = set()
        self._loaded_nested_memory_paths: set[str] = set()

    async def submit_message(
        self,
        prompt: str | list[dict[str, Any]],
        options: dict[str, Any] | None = None,
    ) -> AsyncIterator[SDKMessage]:
        """
        Submit a message and process the response.

        Yields SDK messages as the conversation progresses.
        """
        from ..bootstrap.state import get_session_id, is_session_persistence_disabled
        from ..core.cost_tracker import get_model_usage, get_total_api_duration, get_total_cost_usd
        from ..utils.cwd import set_cwd

        options = options or {}
        prompt_uuid = options.get("uuid")
        is_meta = options.get("is_meta", False)

        self._discovered_skill_names.clear()
        set_cwd(self.config.cwd)
        not is_session_persistence_disabled()
        start_time = _current_time_ms()

        # Get initial app state
        initial_app_state = self.config.get_app_state()

        # Determine model
        main_loop_model = self.config.user_specified_model or _get_main_loop_model()

        # Determine thinking config
        thinking_config = (
            self.config.thinking_config
            if self.config.thinking_config
            else (
                ThinkingConfig(type="adaptive")
                if _should_enable_thinking_by_default()
                else ThinkingConfig(type="disabled")
            )
        )

        # Build system prompt
        system_prompt = await self._build_system_prompt()

        # Process user input
        messages_from_input = await self._process_user_input(
            prompt,
            prompt_uuid,
            is_meta,
        )

        # Add new messages
        self._mutable_messages.extend(messages_from_input)

        # Build system init message
        yield self._build_system_init_message(
            main_loop_model,
            initial_app_state,
        )

        # Check if we should query
        should_query = True
        for msg in messages_from_input:
            if _is_local_command_message(msg):
                should_query = False
                break

        if not should_query:
            # Return early for local commands
            yield SDKResultMessage(
                type="result",
                subtype="success",
                session_id=get_session_id(),
                uuid=str(uuid.uuid4()),
                is_error=False,
                duration_ms=int(_current_time_ms() - start_time),
                duration_api_ms=int(get_total_api_duration()),
                num_turns=len(self._mutable_messages) - 1,
                result="",
                stop_reason=None,
                total_cost_usd=get_total_cost_usd(),
                usage=self._total_usage,
                model_usage=get_model_usage(),
                permission_denials=self._permission_denials,
            )
            return

        # Main query loop
        turn_count = 1
        NonNullableUsage()
        last_stop_reason: str | None = None

        async for message in self._run_query_loop(
            system_prompt,
            thinking_config,
            main_loop_model,
        ):
            yield message

            if message.type == "user":
                turn_count += 1

        # Build final result
        yield SDKResultMessage(
            type="result",
            subtype="success",
            session_id=get_session_id(),
            uuid=str(uuid.uuid4()),
            is_error=False,
            duration_ms=int(_current_time_ms() - start_time),
            duration_api_ms=int(get_total_api_duration()),
            num_turns=turn_count,
            result=self._extract_result_text(),
            stop_reason=last_stop_reason,
            total_cost_usd=get_total_cost_usd(),
            usage=self._total_usage,
            model_usage=get_model_usage(),
            permission_denials=self._permission_denials,
        )

    async def _build_system_prompt(self) -> str:
        """Build the system prompt from all sources."""
        from ..prompts.system import get_system_prompt

        return await get_system_prompt(
            tools=self.config.tools,
            custom_prompt=self.config.custom_system_prompt,
            append_prompt=self.config.append_system_prompt,
        )

    async def _process_user_input(
        self,
        prompt: str | list[dict[str, Any]],
        prompt_uuid: str | None,
        is_meta: bool,
    ) -> list[Message]:
        """Process user input and return messages."""
        from ..types.message import UserMessage

        if isinstance(prompt, str):
            return [
                UserMessage(
                    uuid=prompt_uuid or str(uuid.uuid4()),
                    message={"role": "user", "content": prompt},
                    is_meta=is_meta,
                )
            ]
        else:
            return [
                UserMessage(
                    uuid=prompt_uuid or str(uuid.uuid4()),
                    message={"role": "user", "content": prompt},
                    is_meta=is_meta,
                )
            ]

    def _build_system_init_message(
        self,
        model: str,
        app_state: AppState,
    ) -> SDKMessage:
        """Build the system initialization message."""
        from ..bootstrap.state import get_session_id

        return SDKMessage(
            type="system",
            session_id=get_session_id(),
            uuid=str(uuid.uuid4()),
        )

    async def _run_query_loop(
        self,
        system_prompt: str,
        thinking_config: ThinkingConfig,
        model: str,
    ) -> AsyncIterator[SDKMessage]:
        """Run the main query loop."""
        from ..bootstrap.state import get_session_id

        # Placeholder implementation
        yield SDKMessage(
            type="assistant",
            session_id=get_session_id(),
            uuid=str(uuid.uuid4()),
        )

    def _extract_result_text(self) -> str:
        """Extract the final result text from the conversation."""
        if not self._mutable_messages:
            return ""

        last_message = self._mutable_messages[-1]
        if hasattr(last_message, "message"):
            content = last_message.message.get("content", "")
            if isinstance(content, str):
                return content
            elif isinstance(content, list) and content:
                last_block = content[-1]
                if isinstance(last_block, dict) and last_block.get("type") == "text":
                    return last_block.get("text", "")

        return ""

    def interrupt(self) -> None:
        """Interrupt the current query."""
        if hasattr(self._abort_controller, "abort"):
            self._abort_controller.abort()

    def get_messages(self) -> list[Message]:
        """Get the current messages."""
        return list(self._mutable_messages)

    def get_read_file_state(self) -> FileStateCache:
        """Get the file read state cache."""
        return self._read_file_state

    def get_session_id(self) -> str:
        """Get the current session ID."""
        from ..bootstrap.state import get_session_id

        return get_session_id()

    def set_model(self, model: str) -> None:
        """Set the model for subsequent queries."""
        self.config.user_specified_model = model


async def ask(
    *,
    commands: list[Command],
    prompt: str | list[dict[str, Any]],
    prompt_uuid: str | None = None,
    is_meta: bool = False,
    cwd: str,
    tools: Tools,
    mcp_clients: list[Any] = None,
    verbose: bool = False,
    thinking_config: ThinkingConfig | None = None,
    max_turns: int | None = None,
    max_budget_usd: float | None = None,
    task_budget: dict[str, int] | None = None,
    can_use_tool: Callable[..., Any],
    mutable_messages: list[Message] | None = None,
    get_read_file_cache: Callable[[], FileStateCache] | None = None,
    set_read_file_cache: Callable[[FileStateCache], None] | None = None,
    custom_system_prompt: str | None = None,
    append_system_prompt: str | None = None,
    user_specified_model: str | None = None,
    fallback_model: str | None = None,
    json_schema: dict[str, Any] | None = None,
    get_app_state: Callable[[], AppState],
    set_app_state: Callable[[Callable[[AppState], AppState]], None],
    abort_controller: Any | None = None,
    replay_user_messages: bool = False,
    include_partial_messages: bool = False,
    handle_elicitation: Callable[..., Any] | None = None,
    agents: list[AgentDefinition] | None = None,
    set_sdk_status: Callable[[Any], None] | None = None,
    orphaned_permission: OrphanedPermission | None = None,
) -> AsyncIterator[SDKMessage]:
    """
    Send a single prompt to the Claude API and return the response.

    Convenience wrapper around QueryEngine for one-shot usage.
    """
    engine = QueryEngine(
        QueryEngineConfig(
            cwd=cwd,
            tools=tools,
            commands=commands,
            mcp_clients=mcp_clients or [],
            agents=agents or [],
            can_use_tool=can_use_tool,
            get_app_state=get_app_state,
            set_app_state=set_app_state,
            initial_messages=mutable_messages,
            read_file_cache=get_read_file_cache() if get_read_file_cache else None,
            custom_system_prompt=custom_system_prompt,
            append_system_prompt=append_system_prompt,
            user_specified_model=user_specified_model,
            fallback_model=fallback_model,
            thinking_config=thinking_config,
            max_turns=max_turns,
            max_budget_usd=max_budget_usd,
            task_budget=task_budget,
            json_schema=json_schema,
            verbose=verbose,
            handle_elicitation=handle_elicitation,
            replay_user_messages=replay_user_messages,
            include_partial_messages=include_partial_messages,
            set_sdk_status=set_sdk_status,
            abort_controller=abort_controller,
            orphaned_permission=orphaned_permission,
        )
    )

    try:
        async for message in engine.submit_message(
            prompt,
            {"uuid": prompt_uuid, "is_meta": is_meta},
        ):
            yield message
    finally:
        if set_read_file_cache:
            set_read_file_cache(engine.get_read_file_state())


# Helper functions


def _current_time_ms() -> float:
    """Get current time in milliseconds."""
    import time

    return time.time() * 1000


def _create_abort_controller() -> Any:
    """Create an abort controller."""

    class AbortController:
        def __init__(self):
            self.aborted = False
            self.reason = None

        def abort(self, reason: str = "user"):
            self.aborted = True
            self.reason = reason

    return AbortController()


def _get_main_loop_model() -> str:
    """Get the default main loop model."""
    import os

    return os.getenv("CLAUDE_CODE_MODEL", "claude-sonnet-4-20250514")


def _should_enable_thinking_by_default() -> bool:
    """Check if thinking should be enabled by default."""
    import os

    return os.getenv("CLAUDE_CODE_THINKING", "").lower() in ("true", "1", "adaptive")


def _is_local_command_message(message: Any) -> bool:
    """Check if a message is a local command message."""
    if hasattr(message, "type") and message.type == "system":
        if hasattr(message, "subtype") and message.subtype == "local_command":
            return True
    return False
