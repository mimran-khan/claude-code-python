"""
Teammate inbox polling → formatted turns / permission routing.

Migrated from: hooks/useInboxPoller.ts

The TypeScript hook is ~950 lines and tightly coupled to AppState, mailbox IPC,
swarm backends, and ToolUseConfirm queues. Python callers should implement an
:class:`InboxPollerPort` and drive :func:`run_inbox_poll_once` from a scheduled
task (e.g. every 1s) while mirroring the TS ``poll`` effect body.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class InboxPollerPort(Protocol):
    async def read_unread_messages(self, agent_name: str, team_name: str | None) -> list[Any]: ...

    async def mark_messages_as_read(self, agent_name: str, team_name: str | None) -> None: ...

    def get_app_state_snapshot(self) -> dict[str, Any]: ...

    def set_app_state(self, fn: Callable[[dict[str, Any]], dict[str, Any]]) -> None: ...

    def on_submit_teammate_message(self, formatted: str) -> bool: ...


async def run_inbox_poll_once(port: InboxPollerPort, *, enabled: bool) -> None:
    """Placeholder single tick — extend by porting TS ``poll`` branches incrementally."""
    if not enabled:
        return
    _ = port
