"""
MCP elicitation (user prompts from servers): hooks and result processing.

Migrated from: services/mcp/elicitationHandler.ts

UI queueing and ``Client.set_request_handler`` registration stay in the host
application; this module holds shared types and hook orchestration.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any, Literal, Protocol

logger = logging.getLogger(__name__)

ElicitAction = Literal["accept", "decline", "cancel"]


@dataclass
class ElicitResult:
    action: ElicitAction
    content: dict[str, Any] | None = None


@dataclass
class ElicitationWaitingState:
    action_label: str
    show_cancel: bool = False


@dataclass
class ElicitationRequestEvent:
    server_name: str
    request_id: str | int
    params: dict[str, Any]
    respond: Callable[[ElicitResult], None]
    waiting_state: ElicitationWaitingState | None = None
    on_waiting_dismiss: Callable[[Literal["dismiss", "retry", "cancel"]], None] | None = None
    completed: bool = False


class ElicitationHooks(Protocol):
    async def on_elicitation(
        self,
        *,
        server_name: str,
        message: str,
        requested_schema: dict[str, Any] | None,
        signal: Any,
        mode: Literal["form", "url"],
        url: str | None,
        elicitation_id: str | None,
    ) -> tuple[ElicitResult | None, bool]:
        """Return (response, blocking_error)."""


class ElicitationResultHooks(Protocol):
    async def on_elicitation_result(
        self,
        *,
        server_name: str,
        action: str,
        content: dict[str, Any] | None,
        signal: Any,
        mode: Literal["form", "url"] | None,
        elicitation_id: str | None,
    ) -> tuple[ElicitResult | None, bool]:
        """Return (override_result, blocking_error)."""


class NotificationHooks(Protocol):
    def notify(self, *, message: str, notification_type: str) -> Awaitable[None] | None: ...


def get_elicitation_mode(params: dict[str, Any]) -> Literal["form", "url"]:
    return "url" if params.get("mode") == "url" else "form"


def find_elicitation_in_queue(
    queue: list[ElicitationRequestEvent],
    server_name: str,
    elicitation_id: str,
) -> int:
    for i, e in enumerate(queue):
        if e.server_name != server_name:
            continue
        p = e.params
        if p.get("mode") != "url":
            continue
        if p.get("elicitationId") == elicitation_id:
            return i
    return -1


async def run_elicitation_hooks(
    server_name: str,
    params: dict[str, Any],
    signal: Any,
    hooks: ElicitationHooks | None,
) -> ElicitResult | None:
    if hooks is None:
        return None
    mode = get_elicitation_mode(params)
    url = params.get("url") if isinstance(params.get("url"), str) else None
    eid = params.get("elicitationId") if isinstance(params.get("elicitationId"), str) else None
    msg = str(params.get("message", ""))
    schema = params.get("requestedSchema") if isinstance(params.get("requestedSchema"), dict) else None
    try:
        resp, blocking = await hooks.on_elicitation(
            server_name=server_name,
            message=msg,
            requested_schema=schema,
            signal=signal,
            mode=mode,
            url=url,
            elicitation_id=eid,
        )
        if blocking:
            return ElicitResult(action="decline")
        if resp:
            return resp
    except Exception as exc:
        logger.warning("elicitation_hook_error", extra={"server": server_name, "error": str(exc)})
    return None


async def run_elicitation_result_hooks(
    server_name: str,
    result: ElicitResult,
    signal: Any,
    hooks: ElicitationResultHooks | None,
    mode: Literal["form", "url"] | None = None,
    elicitation_id: str | None = None,
    notify: NotificationHooks | None = None,
) -> ElicitResult:
    if hooks is None:
        if notify:
            await _maybe_await(
                notify.notify(
                    message=f'Elicitation response for server "{server_name}": {result.action}',
                    notification_type="elicitation_response",
                )
            )
        return result
    try:
        override, blocking = await hooks.on_elicitation_result(
            server_name=server_name,
            action=result.action,
            content=result.content,
            signal=signal,
            mode=mode,
            elicitation_id=elicitation_id,
        )
        if blocking:
            if notify:
                await _maybe_await(
                    notify.notify(
                        message=f'Elicitation response for server "{server_name}": decline',
                        notification_type="elicitation_response",
                    )
                )
            return ElicitResult(action="decline")
        final = (
            ElicitResult(
                action=override.action,  # type: ignore[arg-type]
                content=override.content if override.content is not None else result.content,
            )
            if override
            else result
        )
        if notify:
            await _maybe_await(
                notify.notify(
                    message=f'Elicitation response for server "{server_name}": {final.action}',
                    notification_type="elicitation_response",
                )
            )
        return final
    except Exception as exc:
        logger.warning("elicitation_result_hook_error", extra={"server": server_name, "error": str(exc)})
        if notify:
            await _maybe_await(
                notify.notify(
                    message=f'Elicitation response for server "{server_name}": {result.action}',
                    notification_type="elicitation_response",
                )
            )
        return result


async def _maybe_await(x: Any) -> None:
    if x is None:
        return
    await x


def truncate_elicitation_log(obj: Any) -> str:
    try:
        return json.dumps(obj, default=str)[:500]
    except (TypeError, ValueError):
        return str(obj)[:500]


@dataclass
class ElicitationHandlerBundle:
    """Optional bundle for a host app wiring hooks + notifications."""

    elicitation_hooks: ElicitationHooks | None = None
    elicitation_result_hooks: ElicitationResultHooks | None = None
    notification_hooks: NotificationHooks | None = None
    extra: dict[str, Any] = field(default_factory=dict)
