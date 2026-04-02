"""Tests for claude_code.core.tool and claude_code.core.query_engine."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from claude_code.core.query_engine import (
    EMPTY_USAGE,
    NonNullableUsage,
    QueryEngine,
    QueryEngineConfig,
    ThinkingConfig,
)
from claude_code.core.tool import (
    BashProgress,
    HookProgress,
    ProgressMessage,
    Tool,
    ToolResult,
    ToolUseContext,
    filter_tool_progress_messages,
    get_empty_tool_permission_context,
    tool_matches_name,
)


def test_tool_matches_name_primary() -> None:
    assert tool_matches_name({"name": "Bash", "aliases": []}, "Bash") is True
    assert tool_matches_name({"name": "Bash", "aliases": []}, "Other") is False


def test_tool_matches_name_alias() -> None:
    spec = {"name": "Grep", "aliases": ["Search", "Ripgrep"]}
    assert tool_matches_name(spec, "Search") is True
    assert tool_matches_name(spec, "Grep") is True
    assert tool_matches_name(spec, "nope") is False


def test_filter_tool_progress_messages_excludes_hooks() -> None:
    bash = BashProgress(output="x")
    hook = HookProgress(hook_name="h", status="s")
    msgs = [
        ProgressMessage(data=bash),
        ProgressMessage(data=hook),
    ]
    out = filter_tool_progress_messages(msgs)
    assert len(out) == 1
    assert out[0].data.type == "bash"


def test_get_empty_tool_permission_context_defaults() -> None:
    ctx = get_empty_tool_permission_context()
    assert ctx.mode == "default"
    assert ctx.additional_working_directories == {}


class _FakeStream:
    """Minimal async stream stand-in for Anthropic ``messages.stream``."""

    async def __aenter__(self) -> _FakeStream:
        return self

    async def __aexit__(self, *args: object) -> None:
        return None

    @property
    def text_stream(self):
        async def _chunks() -> None:
            yield "hello"

        return _chunks()

    async def get_final_message(self):
        return SimpleNamespace(stop_reason="end_turn", content=[], usage=None)


class _FakeAnthropicMessages:
    def stream(self, **kwargs: object) -> _FakeStream:
        return _FakeStream()


class _FakeAnthropicClient:
    def __init__(self) -> None:
        self.messages = _FakeAnthropicMessages()


class _FakeStreamRound:
    """Single stream response with configurable final message."""

    def __init__(self, *, stop_reason: str, content: list[object], usage: object) -> None:
        self._stop_reason = stop_reason
        self._content = content
        self._usage = usage

    async def __aenter__(self) -> _FakeStreamRound:
        return self

    async def __aexit__(self, *args: object) -> None:
        return None

    @property
    def text_stream(self):
        async def _chunks() -> None:
            for block in self._content:
                if getattr(block, "type", None) == "text":
                    yield block.text

        return _chunks()

    async def get_final_message(self) -> object:
        return SimpleNamespace(
            stop_reason=self._stop_reason,
            content=self._content,
            usage=self._usage,
        )


class _FakeAnthropicMessagesToolLoop:
    def __init__(self) -> None:
        self._round = 0

    def stream(self, **kwargs: object) -> _FakeStreamRound:
        self._round += 1
        usage = SimpleNamespace(
            input_tokens=2,
            output_tokens=3,
            cache_creation_input_tokens=0,
            cache_read_input_tokens=0,
        )
        if self._round == 1:
            content = [
                SimpleNamespace(type="tool_use", name="minimal", id="toolu_01", input={}),
            ]
            return _FakeStreamRound(stop_reason="tool_use", content=content, usage=usage)
        content = [SimpleNamespace(type="text", text="tool_ok")]
        return _FakeStreamRound(stop_reason="end_turn", content=content, usage=usage)


class _FakeAnthropicClientToolLoop:
    def __init__(self) -> None:
        self.messages = _FakeAnthropicMessagesToolLoop()


class _MinimalCoreTool(Tool):
    name = "minimal"
    description = "test"
    input_schema: dict = {}

    async def call(
        self,
        input_data: dict,
        context: ToolUseContext,
        progress_callback=None,
    ) -> ToolResult:
        return ToolResult(data={"ok": True})


@pytest.mark.asyncio
async def test_core_tool_default_validate_and_summary() -> None:
    t = _MinimalCoreTool()
    assert t.validate_input({}).result is True
    assert t.get_tool_use_summary({}) == "minimal(...)"


@pytest.mark.asyncio
async def test_query_engine_submit_message_stream() -> None:
    config = QueryEngineConfig(
        cwd="/tmp",
        tools=[],
        thinking_config=ThinkingConfig(type="disabled"),
        anthropic_client=_FakeAnthropicClient(),  # type: ignore[arg-type]
    )
    engine = QueryEngine(config)
    types: list[str] = []
    async for msg in engine.submit_message("hello world"):
        types.append(msg.type)
    assert types == ["message_start", "text", "message_stop"]


@pytest.mark.asyncio
async def test_query_engine_query_returns_concatenated_text() -> None:
    config = QueryEngineConfig(
        cwd="/tmp",
        tools=[],
        anthropic_client=_FakeAnthropicClient(),  # type: ignore[arg-type]
    )
    engine = QueryEngine(config)
    assert await engine.query("Hello") == "hello"


@pytest.mark.asyncio
async def test_query_engine_tool_use_loop_executes_tool() -> None:
    def _allow(_name: str, _inp: dict) -> dict:
        return {"allowed": True}

    config = QueryEngineConfig(
        cwd="/tmp",
        tools=[_MinimalCoreTool()],
        can_use_tool=_allow,
        anthropic_client=_FakeAnthropicClientToolLoop(),  # type: ignore[arg-type]
    )
    engine = QueryEngine(config)
    types: list[str] = []
    texts: list[str] = []
    async for msg in engine.submit_message("run minimal tool"):
        types.append(msg.type)
        if msg.type == "text" and isinstance(msg.content, str):
            texts.append(msg.content)
    assert "tool_use" in types
    assert "tool_ok" in "".join(texts)


@pytest.mark.asyncio
async def test_query_engine_submit_message_clears_discovered_skills_each_turn() -> None:
    config = QueryEngineConfig(
        cwd="/tmp",
        tools=[],
        anthropic_client=_FakeAnthropicClient(),  # type: ignore[arg-type]
    )
    engine = QueryEngine(config)
    engine._discovered_skill_names.add("skill-a")  # noqa: SLF001 — exercising internal reset
    _ = [m async for m in engine.submit_message("x")]
    assert engine._discovered_skill_names == set()  # noqa: SLF001


def test_query_engine_accumulate_usage() -> None:
    config = QueryEngineConfig(cwd="/tmp", tools=[])
    engine = QueryEngine(config)
    assert engine.total_usage == EMPTY_USAGE
    engine.accumulate_usage(
        NonNullableUsage(
            input_tokens=10,
            output_tokens=5,
            cache_creation_input_tokens=1,
            cache_read_input_tokens=2,
        )
    )
    u = engine.total_usage
    assert u.input_tokens == 10
    assert u.output_tokens == 5
    assert u.cache_creation_input_tokens == 1
    assert u.cache_read_input_tokens == 2
    engine.accumulate_usage(NonNullableUsage(input_tokens=3, output_tokens=0))
    assert engine.total_usage.input_tokens == 13


def test_query_engine_build_tool_use_context_includes_model() -> None:
    config = QueryEngineConfig(
        cwd="/tmp",
        tools=[],
        user_specified_model="claude-opus",
        verbose=True,
    )
    engine = QueryEngine(config)
    ctx = engine._build_tool_use_context()  # noqa: SLF001
    assert ctx.options["main_loop_model"] == "claude-opus"
    assert ctx.options["verbose"] is True
    assert ctx.options["is_non_interactive_session"] is True
