"""Ant-only bridge fault injection (ported from bridge/bridgeDebug.ts)."""

from __future__ import annotations

import logging
from typing import Any, Literal, TypedDict, cast

from claude_code.bridge.bridge_api import BridgeFatalError

logger = logging.getLogger(__name__)


class BridgeFault(TypedDict, total=False):
    method: Literal[
        "pollForWork",
        "registerBridgeEnvironment",
        "reconnectSession",
        "heartbeatWork",
    ]
    kind: Literal["fatal", "transient"]
    status: int
    error_type: str | None
    count: int


class BridgeDebugHandle(TypedDict, total=False):
    fire_close: Any
    force_reconnect: Any
    inject_fault: Any
    wake_poll_loop: Any
    describe: Any


_debug_handle: BridgeDebugHandle | None = None
_fault_queue: list[BridgeFault] = []


def register_bridge_debug_handle(h: BridgeDebugHandle) -> None:
    global _debug_handle
    _debug_handle = h


def clear_bridge_debug_handle() -> None:
    global _debug_handle
    _debug_handle = None
    _fault_queue.clear()


def get_bridge_debug_handle() -> BridgeDebugHandle | None:
    return _debug_handle


def inject_bridge_fault(fault: BridgeFault) -> None:
    _fault_queue.append(fault)
    logger.debug(
        "[bridge:debug] Queued fault: %s %s/%s x%s",
        fault.get("method"),
        fault.get("kind"),
        fault.get("status"),
        fault.get("count"),
    )


def wrap_api_for_fault_injection(api: Any) -> Any:
    def consume(method: str) -> BridgeFault | None:
        for i, f in enumerate(_fault_queue):
            if f.get("method") == method:
                fault = cast(BridgeFault, dict(f))
                c = int(fault.get("count") or 1) - 1
                if c <= 0:
                    _fault_queue.pop(i)
                else:
                    fault["count"] = c
                    _fault_queue[i] = fault
                return cast(BridgeFault, dict(f))
        return None

    def throw_fault(fault: BridgeFault, context: str) -> None:
        logger.debug(
            "[bridge:debug] Injecting %s fault into %s: status=%s",
            fault.get("kind"),
            context,
            fault.get("status"),
        )
        if fault.get("kind") == "fatal":
            raise BridgeFatalError(
                f"[injected] {context} {fault.get('status')}",
                int(fault.get("status") or 0),
                fault.get("error_type"),
            )
        raise RuntimeError(f"[injected transient] {context} {fault.get('status')}")

    class _Wrap:
        def __getattr__(self, name: str) -> Any:
            return getattr(api, name)

        async def poll_for_work(self, *args: Any, **kwargs: Any) -> Any:
            f = consume("pollForWork")
            if f:
                throw_fault(f, "Poll")
            return await api.poll_for_work(*args, **kwargs)

        async def register_bridge_environment(self, *args: Any, **kwargs: Any) -> Any:
            f = consume("registerBridgeEnvironment")
            if f:
                throw_fault(f, "Registration")
            return await api.register_bridge_environment(*args, **kwargs)

        async def reconnect_session(self, *args: Any, **kwargs: Any) -> Any:
            f = consume("reconnectSession")
            if f:
                throw_fault(f, "ReconnectSession")
            return await api.reconnect_session(*args, **kwargs)

        async def heartbeat_work(self, *args: Any, **kwargs: Any) -> Any:
            f = consume("heartbeatWork")
            if f:
                throw_fault(f, "Heartbeat")
            return await api.heartbeat_work(*args, **kwargs)

    return _Wrap()
