"""OAuth redirect port selection for MCP flows.

Migrated from: services/mcp/oauthPort.ts
"""

from __future__ import annotations

import asyncio
import os
import random
import socket


def build_redirect_uri(port: int = 3118) -> str:
    return f"http://localhost:{port}/callback"


def _redirect_port_range() -> tuple[int, int]:
    if os.name == "nt":
        return (39152, 49151)
    return (49152, 65535)


def _configured_callback_port() -> int | None:
    raw = os.environ.get("MCP_OAUTH_CALLBACK_PORT", "")
    if not raw:
        return None
    try:
        p = int(raw, 10)
    except ValueError:
        return None
    return p if p > 0 else None


async def find_available_port() -> int:
    configured = _configured_callback_port()
    if configured is not None:
        return configured
    min_p, max_p = _redirect_port_range()
    span = max_p - min_p + 1
    attempts = min(span, 100)
    for _ in range(attempts):
        port = min_p + random.randint(0, span - 1)
        try:
            await asyncio.to_thread(_try_bind, port)
            return port
        except OSError:
            continue
    try:
        await asyncio.to_thread(_try_bind, 3118)
    except OSError as exc:
        raise RuntimeError("No available ports for OAuth redirect") from exc
    return 3118


def _try_bind(port: int) -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(("127.0.0.1", port))


def find_available_port_sync() -> int:
    """Synchronous port selection for threaded OAuth callbacks (no event loop)."""
    configured = _configured_callback_port()
    if configured is not None:
        return configured
    min_p, max_p = _redirect_port_range()
    span = max_p - min_p + 1
    attempts = min(span, 100)
    for _ in range(attempts):
        port = min_p + random.randint(0, span - 1)
        try:
            _try_bind(port)
            return port
        except OSError:
            continue
    try:
        _try_bind(3118)
    except OSError as exc:
        raise RuntimeError("No available ports for OAuth redirect") from exc
    return 3118
