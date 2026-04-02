#!/usr/bin/env python3
"""
Simple one-shot model query using the service-layer ``query_model`` helper.

This is the smallest reliable path to call the Anthropic Messages API through
this package's client (retries, token limits, etc.). For multi-turn agents with
tools, use ``QueryEngine`` / ``ask`` from ``claude_code.engine`` once your app
wires bootstrap, cwd, and tool registries (see ``docs/API.md``).

Prerequisites:
  - ``ANTHROPIC_API_KEY``

Run:
  python examples/basic_query.py
"""

from __future__ import annotations

import asyncio
import os
import sys
from typing import Any

from _path_setup import ensure_src_on_path

ensure_src_on_path()

from claude_code.services.api.claude import query_model


def _default_model() -> str:
    return (
        os.getenv("ANTHROPIC_MODEL")
        or os.getenv("CLAUDE_CODE_MODEL")
        or "claude-sonnet-4-20250514"
    )


async def main() -> int:
    if not os.getenv("ANTHROPIC_API_KEY", "").strip():
        print(
            "Error: ANTHROPIC_API_KEY is required.\n"
            "Example: export ANTHROPIC_API_KEY=sk-ant-...",
            file=sys.stderr,
        )
        return 1

    model = _default_model()
    messages: list[dict[str, Any]] = [
        {"role": "user", "content": "In one sentence, what is pytest?"},
    ]

    try:
        result = await query_model(
            messages=messages,
            model=model,
            system="Answer briefly.",
            tools=None,
            temperature=0.2,
        )
    except Exception as exc:
        print(f"API request failed: {exc}", file=sys.stderr)
        return 1

    try:
        content = result.message.get("content", [])
        texts: list[str] = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                texts.append(str(block.get("text", "")))
        answer = "\n".join(texts).strip() or str(content)

        print("--- assistant ---")
        print(answer)
        print("\n--- usage ---")
        print(f"input_tokens: {result.input_tokens}")
        print(f"output_tokens: {result.output_tokens}")
        print(f"stop_reason: {result.stop_reason}")
        print(f"model: {result.model}")
    except (KeyError, TypeError, AttributeError) as exc:
        print(f"Could not parse response: {exc}", file=sys.stderr)
        print(f"Raw message payload: {result.message!r}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
