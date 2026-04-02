#!/usr/bin/env python3
"""
Stream raw model events via ``query_model_with_streaming``.

This uses the service-layer Anthropic client (not the full QueryEngine loop), which is
the right integration point when you only need token streaming.

Prerequisites:
  - ``ANTHROPIC_API_KEY``

Run:
  python examples/streaming.py
"""

from __future__ import annotations

import asyncio
import os
import sys
from typing import Any

from _path_setup import ensure_src_on_path

ensure_src_on_path()

from claude_code.services.api.claude import StreamEvent, query_model_with_streaming


def _default_model() -> str:
    return (
        os.getenv("ANTHROPIC_MODEL")
        or os.getenv("CLAUDE_CODE_MODEL")
        or "claude-sonnet-4-20250514"
    )


async def main() -> int:
    if not os.getenv("ANTHROPIC_API_KEY", "").strip():
        print("Error: ANTHROPIC_API_KEY is required for streaming.", file=sys.stderr)
        return 1

    model = _default_model()
    messages: list[dict[str, Any]] = [
        {"role": "user", "content": "Write exactly two short sentences about Python asyncio."},
    ]

    buffer: list[str] = []

    def on_event(ev: StreamEvent) -> None:
        """Optional side channel for metrics/logging (keep callbacks cheap)."""
        if ev.type == "error" and ev.error:
            print(f"[callback] error event: {ev.error}", file=sys.stderr)

    try:
        async for event in query_model_with_streaming(
            messages=messages,
            model=model,
            system="Be concise.",
            tools=None,
            on_event=on_event,
        ):
            if event.type == "error":
                print(f"\nStream error: {event.error}", file=sys.stderr)
                return 1

            if event.type == "content_block_delta" and event.delta:
                delta = event.delta
                if isinstance(delta, dict) and delta.get("type") == "text_delta":
                    piece = str(delta.get("text", ""))
                    buffer.append(piece)
                    sys.stdout.write(piece)
                    sys.stdout.flush()

            if event.type == "message_stop":
                break

        print()
        if not buffer:
            print("Warning: no text deltas received (model or transport may differ).", file=sys.stderr)

    except Exception as exc:
        print(f"Streaming failed: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
