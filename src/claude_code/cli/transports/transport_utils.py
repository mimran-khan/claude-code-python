"""
Select WebSocket, hybrid, or SSE transport from URL and environment.

Migrated from: cli/transports/transportUtils.ts
"""

from __future__ import annotations

from collections.abc import Callable
from urllib.parse import urlparse, urlunparse

from .hybrid_transport import HybridTransport
from .session_ingress_headers import is_env_truthy
from .sse_transport import SSETransport
from .transport_base import Transport
from .websocket_transport import WebSocketTransport, WebSocketTransportOptions


def get_transport_for_url(
    url: str,
    headers: dict[str, str] | None = None,
    session_id: str | None = None,
    refresh_headers: Callable[[], dict[str, str]] | None = None,
) -> Transport:
    h = dict(headers or {})
    p = urlparse(url)

    if is_env_truthy("CLAUDE_CODE_USE_CCR_V2"):
        sse_url = url
        pr = urlparse(sse_url)
        scheme = "https" if pr.scheme == "wss" else "http" if pr.scheme == "ws" else pr.scheme
        path = pr.path.rstrip("/") + "/worker/events/stream"
        sse_url = urlunparse((scheme, pr.netloc, path, "", pr.query, ""))
        return SSETransport(
            sse_url,
            headers=h,
            session_id=session_id,
            refresh_headers=refresh_headers,
        )

    if p.scheme in ("ws", "wss"):
        if is_env_truthy("CLAUDE_CODE_POST_FOR_SESSION_INGRESS_V2"):
            return HybridTransport(
                url,
                headers=h,
                session_id=session_id,
                refresh_headers=refresh_headers,
                options=WebSocketTransportOptions(),
            )
        return WebSocketTransport(
            url,
            headers=h,
            session_id=session_id,
            refresh_headers=refresh_headers,
            options=WebSocketTransportOptions(),
        )

    raise ValueError(f"Unsupported protocol: {p.scheme}")
