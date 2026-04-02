"""Core query engine: Anthropic-backed conversation loop and tool execution.

This module defines :class:`QueryEngine`, configuration dataclasses, and message
shapes used with :mod:`claude_code.core.tool` (``AppState``, ``Tool``,
``ToolUseContext``).

**When to use this module**

* Extend low-level tooling that imports ``claude_code.core`` and must match
  these dataclass definitions.

**When to prefer** :mod:`claude_code.engine.query_engine`

* The CLI and package-level API typically use the engine implementation there
  (e.g. ``from claude_code import QueryEngine``).

Migrated from: ``QueryEngine.ts`` (partial / core extraction).
"""

from __future__ import annotations

from collections.abc import AsyncGenerator, Callable
from dataclasses import dataclass, field
from typing import (
    Any,
    cast,
)

from anthropic import NOT_GIVEN, AsyncAnthropic

from .query_engine_anthropic import (
    append_initial_api_messages,
    build_async_client,
    execute_tool_uses,
    is_abort_event,
    normalize_user_content,
    resolve_api_key,
    tools_to_anthropic_params,
    usage_from_message,
)
from .tool import (
    AppState,
    FileStateCache,
    Tool,
    ToolUseContext,
)


@dataclass
class ThinkingConfig:
    """Extended thinking mode settings for the Messages API.

    Attributes:
        type: One of the strings ``disabled``, ``adaptive``, or ``always``.
    """

    type: str = "disabled"  # "disabled", "adaptive", "always"


@dataclass
class MCPServerConnection:
    """Metadata for an MCP server slot (connection state and optional hints).

    Attributes:
        name: Logical server name from configuration.
        type: Connection state label (e.g. ``connected``, ``disconnected``, ``error``).
        instructions: Optional server-supplied instructions for the model.
    """

    name: str
    type: str = "disconnected"  # "connected", "disconnected", "error"
    instructions: str | None = None


@dataclass
class AgentDefinition:
    """Declarative agent entry exposed to the tool context.

    Attributes:
        name: Unique agent identifier.
        agent_type: Agent kind or routing label.
        description: Human-readable summary for prompts and UIs.
    """

    name: str
    agent_type: str
    description: str


@dataclass
class Command:
    """Slash or custom command available in the session.

    Attributes:
        name: Command trigger name.
        description: Short explanation shown to the model or user.
    """

    name: str
    description: str


@dataclass
class NonNullableUsage:
    """Cumulative token usage with non-optional integer fields.

    Attributes:
        input_tokens: Prompt tokens consumed.
        output_tokens: Completion tokens produced.
        cache_creation_input_tokens: Tokens written to the prompt cache.
        cache_read_input_tokens: Tokens read from the prompt cache.
    """

    input_tokens: int = 0
    output_tokens: int = 0
    cache_creation_input_tokens: int = 0
    cache_read_input_tokens: int = 0


EMPTY_USAGE = NonNullableUsage()


@dataclass
class SDKPermissionDenial:
    """Record of a tool call blocked by host permission policy.

    Attributes:
        tool_name: Name of the tool that was denied.
        tool_use_id: Provider tool-use id from the assistant message.
        tool_input: Parsed tool arguments at denial time.
    """

    tool_name: str
    tool_use_id: str
    tool_input: dict[str, Any]


@dataclass
class QueryEngineConfig:
    """Full static configuration for :class:`QueryEngine`.

    Attributes:
        cwd: Working directory for tools and relative paths.
        tools: Registered :class:`~claude_code.core.tool.Tool` instances.
        commands: Custom commands passed into tool context.
        mcp_clients: MCP server connection descriptors.
        agents: Agent definitions for multi-agent contexts.
        can_use_tool: Optional callback to approve or deny tool calls.
        get_app_state: Optional accessor for mutable :class:`~claude_code.core.tool.AppState`.
        set_app_state: Optional functional updater for app state.
        initial_messages: Seed conversation; merged into API and mutable lists.
        read_file_cache: Shared file snapshot cache for tools.
        custom_system_prompt: Replaces default system prompt when set.
        append_system_prompt: Additional system text appended after custom prompt.
        user_specified_model: Primary model id override.
        fallback_model: Reserved for fallback selection (host-specific).
        thinking_config: Thinking mode configuration.
        max_turns: Upper bound on assistant/tool loops per user message.
        max_budget_usd: Optional spend ceiling (host-enforced).
        task_budget: Optional per-task budgets (host-specific).
        json_schema: Optional structured-output schema (host-specific).
        verbose: Enable verbose diagnostics in tool context.
        replay_user_messages: Replay behavior for user messages (host-specific).
        handle_elicitation: Optional MCP elicitation handler.
        include_partial_messages: Include partial stream payloads (host-specific).
        set_sdk_status: Optional status line callback.
        abort_controller: Object with ``abort()`` to cancel in-flight work.
        orphaned_permission: Handler for orphaned permission flows (host-specific).
        snip_replay: Optional replay trimming hook.
        api_key: Anthropic API key override (else env/default).
        base_url: API base URL override.
        max_tokens: Per-completion max tokens.
        enable_streaming: Use streaming API when True.
        anthropic_client: Injected :class:`~anthropic.AsyncAnthropic` for tests.
    """

    cwd: str
    tools: list[Tool]
    commands: list[Command] = field(default_factory=list)
    mcp_clients: list[MCPServerConnection] = field(default_factory=list)
    agents: list[AgentDefinition] = field(default_factory=list)
    can_use_tool: Callable[..., Any] | None = None
    get_app_state: Callable[[], AppState] | None = None
    set_app_state: Callable[[Callable[[AppState], AppState]], None] | None = None
    initial_messages: list[Any] | None = None
    read_file_cache: FileStateCache = field(default_factory=FileStateCache)
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
    set_sdk_status: Callable[[str], None] | None = None
    abort_controller: Any | None = None
    orphaned_permission: Any | None = None
    snip_replay: Callable[..., Any] | None = None
    # Anthropic Messages API
    api_key: str | None = None
    base_url: str | None = None
    max_tokens: int = 4096
    enable_streaming: bool = True
    anthropic_client: AsyncAnthropic | None = None


@dataclass
class SDKMessage:
    """Streaming or step event emitted by :meth:`QueryEngine.submit_message`.

    Attributes:
        type: Event kind (e.g. ``text``, ``tool_use``, ``message_start``,
            ``message_stop``, ``error``).
        content: Payload; structure depends on ``type`` (str, dict, or list).
    """

    type: str
    content: Any


class QueryEngine:
    """Runs the user/assistant/tool loop against the Anthropic Messages API.

    Holds mutable conversation state (API message list, usage, permission
    denials, file cache pointers) for a single session. Each
    :meth:`submit_message` processes one user turn, which may include multiple
    model rounds if the model requests tool use.

    One instance per conversation; message and usage state persist across
    turns until the instance is discarded.

    Note:
        For the CLI-facing engine with richer types, see
        :mod:`claude_code.engine.query_engine`.
    """

    def __init__(self, config: QueryEngineConfig) -> None:
        """Create an engine bound to ``config``.

        Args:
            config: Static wiring for tools, model, callbacks, and initial messages.
        """
        self._config = config
        self._mutable_messages: list[Any] = list(config.initial_messages) if config.initial_messages else []
        self._abort_controller = config.abort_controller
        self._permission_denials: list[SDKPermissionDenial] = []
        self._total_usage = EMPTY_USAGE
        self._has_handled_orphaned_permission = False
        self._read_file_state = config.read_file_cache
        self._discovered_skill_names: set[str] = set()
        self._loaded_nested_memory_paths: set[str] = set()
        self._api_messages: list[dict[str, Any]] = []
        append_initial_api_messages(config.initial_messages, self._api_messages)

    def _default_system_prompt(self) -> str:
        """Build the system string from custom/append prompts or the default assistant text.

        Returns:
            Text passed as ``system=`` to the Messages API.
        """
        parts: list[str] = []
        if self._config.custom_system_prompt:
            parts.append(self._config.custom_system_prompt)
        if self._config.append_system_prompt:
            parts.append(self._config.append_system_prompt)
        if parts:
            return "\n\n".join(parts)
        return "You are Claude Code, a helpful AI coding assistant. Be concise and accurate."

    def _max_turns_limit(self) -> int:
        """Effective cap on tool/assistant iterations per user message.

        Returns:
            ``max_turns`` from config if positive, otherwise ``32``.
        """
        if self._config.max_turns is not None and self._config.max_turns > 0:
            return self._config.max_turns
        return 32

    def _model_name(self) -> str:
        """Resolve the model id for API calls.

        Returns:
            ``user_specified_model`` if set, else a default Sonnet snapshot id.
        """
        return self._config.user_specified_model or "claude-sonnet-4-20250514"

    def _get_client(self) -> AsyncAnthropic:
        """Return the async Anthropic client (injected or built from config).

        Returns:
            Shared :class:`~anthropic.AsyncAnthropic` instance for this engine.

        Raises:
            anthropic.AuthenticationError: If API key resolution fails in the
                client library (when not using an injected client).
        """
        injected = self._config.anthropic_client
        if injected is not None:
            return injected
        key = resolve_api_key(self._config.api_key)
        return build_async_client(
            api_key=key,
            base_url=self._config.base_url,
            injected=None,
        )

    async def query(self, prompt: str) -> str:
        """Run a single user turn and return only concatenated assistant text.

        Collects ``SDKMessage`` chunks with ``type == "text"`` from
        :meth:`submit_message`; ignores structured tool events for this helper.

        Args:
            prompt: User message text.

        Returns:
            Combined assistant text for the turn (empty if no text blocks).
        """
        parts: list[str] = []
        async for msg in self.submit_message(prompt):
            if msg.type == "text" and isinstance(msg.content, str):
                parts.append(msg.content)
        return "".join(parts)

    @property
    def messages(self) -> list[Any]:
        """Mutable conversation history (user/assistant/tool blocks).

        Returns:
            The same list mutated by :meth:`submit_message`; API-shaped dicts.
        """
        return self._mutable_messages

    @property
    def total_usage(self) -> NonNullableUsage:
        """Cumulative token usage across all completed API calls.

        Returns:
            Totals updated by :meth:`accumulate_usage`.
        """
        return self._total_usage

    @property
    def permission_denials(self) -> list[SDKPermissionDenial]:
        """Tool calls denied by ``can_use_tool`` during this session.

        Returns:
            Append-only list of denials from tool execution.
        """
        return self._permission_denials

    async def submit_message(
        self,
        prompt: str | list[Any],
        options: dict[str, Any] | None = None,
    ) -> AsyncGenerator[SDKMessage, None]:
        """Drive one user turn: model completion, optional tools, then stop.

        Appends the user message, calls Anthropic (stream or non-stream), executes
        any requested tools until the model stops without tool use or limits are
        hit, and yields progress events throughout.

        Args:
            prompt: User content as a string or list of content blocks.
            options: Reserved for host metadata (e.g. uuid); currently unused
                in the core loop.

        Yields:
            :class:`SDKMessage` instances (text deltas, tool_use summaries,
            lifecycle markers, errors).

        Raises:
            anthropic.APIError: On transport/API failures from the Anthropic
                client (propagated from ``messages.create`` / ``stream``).
        """
        options = options or {}

        self._discovered_skill_names.clear()
        context = self._build_tool_use_context()
        system_prompt = self._default_system_prompt()
        model = self._model_name()
        max_tokens = self._config.max_tokens
        tools_param = tools_to_anthropic_params(self._config.tools) if self._config.tools else NOT_GIVEN

        yield SDKMessage(type="message_start", content={})

        user_content = normalize_user_content(prompt)
        user_message: dict[str, Any] = {"role": "user", "content": user_content}
        self._api_messages.append(user_message)
        self._mutable_messages.append(user_message)

        client = self._get_client()
        turn_budget = self._max_turns_limit()

        final: Any
        for _ in range(turn_budget):
            if is_abort_event(self._abort_controller):
                yield SDKMessage(type="error", content="aborted")
                break

            if self._config.enable_streaming:
                async with client.messages.stream(
                    model=model,
                    max_tokens=max_tokens,
                    system=system_prompt,
                    messages=cast(Any, self._api_messages),
                    tools=cast(Any, tools_param),
                ) as stream:
                    async for text in stream.text_stream:
                        yield SDKMessage(type="text", content=text)
                    final = await stream.get_final_message()
            else:
                final = await client.messages.create(
                    model=model,
                    max_tokens=max_tokens,
                    system=system_prompt,
                    messages=cast(Any, self._api_messages),
                    tools=cast(Any, tools_param),
                )
                for block in final.content:
                    if block.type == "text":
                        yield SDKMessage(type="text", content=block.text)

            self.accumulate_usage(usage_from_message(final))

            if final.stop_reason == "tool_use":
                yield SDKMessage(
                    type="tool_use",
                    content=[
                        {"name": b.name, "id": b.id, "input": b.input} for b in final.content if b.type == "tool_use"
                    ],
                )
                self._api_messages.append(
                    {"role": "assistant", "content": final.content},
                )
                self._mutable_messages.append({"role": "assistant", "content": final.content})

                tool_blocks = await execute_tool_uses(
                    message=final,
                    tools=self._config.tools,
                    context=context,
                    can_use_tool=self._config.can_use_tool,
                    permission_denials=self._permission_denials,
                )
                if not tool_blocks:
                    break
                tool_user_msg = {"role": "user", "content": tool_blocks}
                self._api_messages.append(tool_user_msg)
                self._mutable_messages.append(tool_user_msg)
                continue

            self._api_messages.append({"role": "assistant", "content": final.content})
            self._mutable_messages.append({"role": "assistant", "content": final.content})
            break

        yield SDKMessage(type="message_stop", content={})

    def _build_tool_use_context(self) -> ToolUseContext:
        """Assemble :class:`~claude_code.core.tool.ToolUseContext` from config.

        Returns:
            Context passed into :func:`~claude_code.core.query_engine_anthropic.execute_tool_uses`.
        """
        return ToolUseContext(
            options={
                "commands": self._config.commands,
                "debug": False,
                "main_loop_model": self._config.user_specified_model or "claude-sonnet-4-20250514",
                "tools": self._config.tools,
                "verbose": self._config.verbose,
                "thinking_config": self._config.thinking_config or ThinkingConfig(),
                "mcp_clients": self._config.mcp_clients,
                "mcp_resources": {},
                "is_non_interactive_session": True,
                "agent_definitions": {"agents": self._config.agents, "agentErrors": []},
                "max_budget_usd": self._config.max_budget_usd,
                "custom_system_prompt": self._config.custom_system_prompt,
                "append_system_prompt": self._config.append_system_prompt,
            },
            abort_controller=self._abort_controller,
            read_file_state=self._read_file_state,
            get_app_state=self._config.get_app_state or (lambda: AppState()),
            set_app_state=self._config.set_app_state or (lambda f: None),
            messages=self._mutable_messages,
            set_in_progress_tool_use_ids=lambda f: None,
            set_response_length=lambda f: None,
            update_file_history_state=lambda f: None,
            update_attribution_state=lambda f: None,
        )

    def abort(self) -> None:
        """Signal in-flight work to stop if ``abort_controller`` supports ``abort``."""
        if self._abort_controller and hasattr(self._abort_controller, "abort"):
            self._abort_controller.abort()

    def accumulate_usage(self, usage: NonNullableUsage) -> None:
        """Add one completion's token counts into :attr:`total_usage`.

        Args:
            usage: Delta usage from a single API response.
        """
        self._total_usage = NonNullableUsage(
            input_tokens=self._total_usage.input_tokens + usage.input_tokens,
            output_tokens=self._total_usage.output_tokens + usage.output_tokens,
            cache_creation_input_tokens=(
                self._total_usage.cache_creation_input_tokens + usage.cache_creation_input_tokens
            ),
            cache_read_input_tokens=(self._total_usage.cache_read_input_tokens + usage.cache_read_input_tokens),
        )
