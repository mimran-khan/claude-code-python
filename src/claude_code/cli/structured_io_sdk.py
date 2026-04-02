"""
SDK structured stdin/stdout (NDJSON) for headless / print mode.

Migrated from: cli/structuredIO.ts (line parsing, prepend, stdout writes; condensed).
"""

from __future__ import annotations

import json
import sys
from collections.abc import AsyncIterator
from typing import Any

from .ndjson_safe_stringify import ndjson_safe_stringify

SANDBOX_NETWORK_ACCESS_TOOL_NAME = "SandboxNetworkAccess"


def _write_stdout_line(obj: dict[str, Any]) -> None:
    sys.stdout.write(ndjson_safe_stringify(obj) + "\n")
    sys.stdout.flush()


async def iter_ndjson_messages(
    line_source: AsyncIterator[str],
    *,
    replay_user_messages: bool = False,
) -> AsyncIterator[dict[str, Any]]:
    """
    Yield parsed SDK messages from an async stream of text chunks (TS read() core).
    """
    content = ""
    prepended: list[str] = []

    def pull_prepended() -> None:
        nonlocal content
        if prepended:
            content = "".join(prepended) + content
            prepended.clear()

    async def drain_buffer() -> AsyncIterator[dict[str, Any]]:
        nonlocal content
        pull_prepended()
        while "\n" in content:
            line, content = content.split("\n", 1)
            msg = _process_line(line, replay_user_messages=replay_user_messages)
            if msg is not None:
                yield msg

    async for block in line_source:
        content += block
        async for m in drain_buffer():
            yield m
    pull_prepended()
    if content:
        msg = _process_line(content, replay_user_messages=replay_user_messages)
        if msg is not None:
            yield msg


def push_prepended_user_line(prepended: list[str], content: str) -> None:
    line = (
        json.dumps(
            {
                "type": "user",
                "session_id": "",
                "message": {"role": "user", "content": content},
                "parent_tool_use_id": None,
            },
            ensure_ascii=False,
        )
        + "\n"
    )
    prepended.append(line)


def _process_line(
    line: str,
    *,
    replay_user_messages: bool,
) -> dict[str, Any] | None:
    if not line:
        return None
    try:
        message: dict[str, Any] = json.loads(line)
    except json.JSONDecodeError as e:
        print(f"Error parsing streaming input line: {line}: {e}", file=sys.stderr)
        sys.exit(1)
    mtype = message.get("type")
    if mtype == "keep_alive":
        return None
    if mtype == "update_environment_variables":
        variables = message.get("variables") or {}
        if isinstance(variables, dict):
            import os

            for k, v in variables.items():
                if isinstance(k, str) and isinstance(v, str):
                    os.environ[k] = v
        return None
    if mtype == "control_response":
        if replay_user_messages:
            return message
        return None
    if mtype not in ("user", "control_request", "assistant", "system"):
        return None
    if mtype == "control_request" and not message.get("request"):
        print("Error: Missing request on control_request", file=sys.stderr)
        sys.exit(1)
    if mtype in ("assistant", "system"):
        return message
    role = (message.get("message") or {}).get("role")
    if role != "user":
        print(f"Error: Expected message role 'user', got '{role}'", file=sys.stderr)
        sys.exit(1)
    return message


class StructuredIOSDK:
    """Buffers prepended user lines and exposes async message iteration + write."""

    def __init__(
        self,
        line_source: AsyncIterator[str],
        replay_user_messages: bool = False,
    ) -> None:
        self._line_source = line_source
        self._replay = replay_user_messages
        self._prepended: list[str] = []

    def prepend_user_message(self, content: str) -> None:
        push_prepended_user_line(self._prepended, content)

    async def messages(self) -> AsyncIterator[dict[str, Any]]:
        async def merged_source() -> AsyncIterator[str]:
            if self._prepended:
                yield "".join(self._prepended)
                self._prepended.clear()
            async for chunk in self._line_source:
                yield chunk

        async for msg in iter_ndjson_messages(
            merged_source(),
            replay_user_messages=self._replay,
        ):
            yield msg

    async def write(self, message: dict[str, Any]) -> None:
        _write_stdout_line(message)

    async def flush_internal_events(self) -> None:
        return None

    @property
    def internal_events_pending(self) -> int:
        return 0
