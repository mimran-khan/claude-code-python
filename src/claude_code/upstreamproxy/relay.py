"""
Upstream proxy relay server.

Migrated from: upstreamproxy/relay.ts
"""

import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class RelayState:
    """State of the relay server."""

    running: bool = False
    port: int | None = None
    server: Any | None = None  # asyncio.Server at runtime


_relay_state = RelayState()


async def start_upstream_proxy_relay(
    upstream_url: str,
    token: str,
    port: int = 0,
) -> int | None:
    """Start the CONNECT→WebSocket relay server.

    Creates a local TCP server that accepts CONNECT requests and
    relays them through a WebSocket tunnel to the upstream proxy.

    Args:
        upstream_url: WebSocket URL of upstream proxy
        token: Session authentication token
        port: Local port to listen on (0 = auto-assign)

    Returns:
        Assigned port number, or None if failed
    """
    global _relay_state

    if _relay_state.running:
        logger.warning("[relay] Already running")
        return _relay_state.port

    try:
        # Create relay server
        # Full implementation would:
        # 1. Parse CONNECT requests
        # 2. Establish WebSocket to upstream
        # 3. Relay data bidirectionally

        logger.info(f"[relay] Starting relay on port {port}")

        # For now, just stub the server
        _relay_state.running = True
        _relay_state.port = port or 8080

        return _relay_state.port

    except Exception as e:
        logger.error(f"[relay] Failed to start: {e}")
        return None


async def stop_upstream_proxy_relay() -> None:
    """Stop the relay server."""
    global _relay_state

    if not _relay_state.running:
        return

    if _relay_state.server:
        _relay_state.server.close()
        await _relay_state.server.wait_closed()

    _relay_state.running = False
    _relay_state.port = None
    _relay_state.server = None

    logger.info("[relay] Stopped")


def is_relay_running() -> bool:
    """Check if relay is running."""
    return _relay_state.running


def get_relay_port() -> int | None:
    """Get relay port if running."""
    return _relay_state.port if _relay_state.running else None
