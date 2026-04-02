"""Live Anthropic API checks for core QueryEngine (requires ANTHROPIC_API_KEY)."""

from __future__ import annotations

import os

import pytest

from claude_code.core.query_engine import QueryEngine, QueryEngineConfig


@pytest.mark.integration
@pytest.mark.asyncio
async def test_query_engine_live_query_hello() -> None:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        pytest.skip("ANTHROPIC_API_KEY not set")
    config = QueryEngineConfig(
        cwd=os.getcwd(),
        tools=[],
        enable_streaming=True,
        max_tokens=256,
    )
    engine = QueryEngine(config)
    reply = await engine.query(
        "Reply with a single short sentence confirming you are working. "
        "Do not use tools."
    )
    assert len(reply.strip()) > 0
    assert engine.total_usage.output_tokens > 0
