"""Spawn child Claude sessions for the bridge (ported from bridge/sessionRunner.ts)."""

from __future__ import annotations

import asyncio
import json
import logging
import re
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, TypedDict

from claude_code.bridge.debug_utils import debug_truncate
from claude_code.bridge.types import (
    SessionActivity,
    SessionHandle,
    SessionSpawner,
    SessionSpawnOpts,
)

logger = logging.getLogger(__name__)
MAX_ACTIVITIES = 10
MAX_STDERR_LINES = 10

TOOL_VERBS: dict[str, str] = {
    "Read": "Reading",
    "Write": "Writing",
    "Edit": "Editing",
    "Bash": "Running",
    "Glob": "Searching",
    "Grep": "Searching",
}


class PermissionRequest(TypedDict, total=False):
    type: str
    request_id: str
    request: dict[str, Any]


def safe_filename_id(id: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_-]", "_", id)


def _tool_summary(name: str, input: dict[str, Any]) -> str:
    verb = TOOL_VERBS.get(name, name)
    target = (
        input.get("file_path")
        or input.get("filePath")
        or input.get("pattern")
        or (str(input.get("command", ""))[:60] if input.get("command") else "")
        or input.get("url")
        or input.get("query")
        or ""
    )
    return f"{verb} {target}" if target else verb


def _extract_activities(
    line: str,
    session_id: str,
    on_debug: Callable[[str], None],
) -> list[SessionActivity]:
    try:
        msg = json.loads(line)
    except Exception:
        return []
    if not isinstance(msg, dict):
        return []
    activities: list[SessionActivity] = []
    now = int(__import__("time").time() * 1000)
    if msg.get("type") == "assistant":
        inner = msg.get("message")
        if not isinstance(inner, dict):
            return []
        content = inner.get("content")
        if not isinstance(content, list):
            return []
        for block in content:
            if not isinstance(block, dict):
                continue
            if block.get("type") == "tool_use":
                name = str(block.get("name") or "Tool")
                inp = block.get("input")
                inp_d = inp if isinstance(inp, dict) else {}
                summary = _tool_summary(name, inp_d)
                activities.append(
                    SessionActivity(
                        type="tool_start",
                        summary=summary,
                        timestamp=now,
                    )
                )
                on_debug(f"[bridge:activity] sessionId={session_id} tool_use name={name} {debug_truncate(str(inp_d))}")
            elif block.get("type") == "text":
                text = str(block.get("text") or "")
                if text:
                    activities.append(SessionActivity(type="text", summary=text[:80], timestamp=now))
    elif msg.get("type") == "result":
        st = msg.get("subtype")
        if st == "success":
            activities.append(
                SessionActivity(
                    type="result",
                    summary="Session completed",
                    timestamp=now,
                )
            )
        elif st:
            errs = msg.get("errors")
            es = errs[0] if isinstance(errs, list) and errs else f"Error: {st}"
            activities.append(SessionActivity(type="error", summary=str(es), timestamp=now))
    return activities


@dataclass
class SessionSpawnerDeps:
    exec_path: str
    script_args: list[str]
    env: dict[str, str]
    verbose: bool
    sandbox: bool
    debug_file: str | None = None
    permission_mode: str | None = None
    on_debug: Callable[[str], None] = field(default_factory=lambda: lambda _m: None)
    on_activity: Callable[[str, SessionActivity], None] | None = None
    on_permission_request: Callable[..., Any] | None = None


def create_session_spawner(deps: SessionSpawnerDeps) -> SessionSpawner:
    @dataclass
    class _StubHandle(SessionHandle):
        def kill(self) -> None:
            t = self.done
            if isinstance(t, asyncio.Task) and not t.done():
                t.cancel()

        def force_kill(self) -> None:
            self.kill()

        def write_stdin(self, data: str) -> None:
            pass

    class _Spawner(SessionSpawner):
        def spawn(self, opts: SessionSpawnOpts, dir: str) -> SessionHandle:
            # TODO: subprocess spawn parity with Node child_process (stdio, env, transcript)
            deps.on_debug(f"[bridge:session] spawn stub sessionId={opts.session_id} dir={dir}")

            async def _done() -> str:
                return "completed"

            return _StubHandle(
                session_id=opts.session_id,
                done=asyncio.create_task(_done()),
                activities=[],
                access_token=opts.access_token,
            )

    return _Spawner()


def _extract_activities_for_testing(line: str, session_id: str) -> list[SessionActivity]:
    return _extract_activities(line, session_id, lambda _m: None)


extract_activities_for_testing = _extract_activities_for_testing
