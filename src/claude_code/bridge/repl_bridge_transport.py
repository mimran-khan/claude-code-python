"""REPL bridge transport implementations (ported from TypeScript bridge/replBridgeTransport.ts)."""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from typing import Any, Protocol

import httpx
import websockets

logger = logging.getLogger(__name__)

# Override path templates if your bridge API differs (placeholders: {base}, {session_id}).
_DEFAULT_V1_SEND = "/api/bridge/v1/sessions/{session_id}/message"
_DEFAULT_V1_RECV = "/api/bridge/v1/sessions/{session_id}/poll"


def _v1_send_path() -> str:
    return os.environ.get("CLAUDE_BRIDGE_V1_SEND_PATH", _DEFAULT_V1_SEND)


def _v1_recv_path() -> str:
    return os.environ.get("CLAUDE_BRIDGE_V1_RECV_PATH", _DEFAULT_V1_RECV)


class ReplBridgeTransport(Protocol):
    """Protocol for REPL bridge transports (v1 or v2)."""

    async def send(self, message: dict[str, Any]) -> None:
        """Send a message through the transport."""
        ...

    async def receive(self) -> dict[str, Any]:
        """Receive a message from the transport."""
        ...

    async def close(self) -> None:
        """Close the transport connection."""
        ...

    @property
    def is_connected(self) -> bool:
        """Check if transport is connected."""
        ...


@dataclass
class V1ReplTransport:
    """V1 transport using HTTP POST (send) and long-poll GET (receive)."""

    base_url: str
    session_id: str
    access_token: str
    _connected: bool = field(default=False, init=False)
    _client: httpx.AsyncClient | None = field(default=None, init=False)

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _full_url(self, template: str) -> str:
        path = template.format(base=self.base_url, session_id=self.session_id)
        if path.startswith("http://") or path.startswith("https://"):
            return path
        base = self.base_url.rstrip("/")
        return f"{base}/{path.lstrip('/')}"

    async def _ensure_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                headers=self._headers(),
                timeout=httpx.Timeout(60.0, connect=10.0),
            )
        return self._client

    async def send(self, message: dict[str, Any]) -> None:
        """Send message via HTTP POST."""
        client = await self._ensure_client()
        url = self._full_url(_v1_send_path())
        resp = await client.post(url, json=message)
        resp.raise_for_status()
        self._connected = True

    async def receive(self) -> dict[str, Any]:
        """Poll for messages via HTTP GET."""
        client = await self._ensure_client()
        url = self._full_url(_v1_recv_path())
        resp = await client.get(url)
        if resp.status_code == 204:
            return {}
        resp.raise_for_status()
        if not resp.content:
            return {}
        try:
            data = resp.json()
        except json.JSONDecodeError:
            logger.warning("bridge_v1_poll_non_json", extra={"text": resp.text[:200]})
            return {"raw": resp.text}
        return data if isinstance(data, dict) else {"data": data}

    async def close(self) -> None:
        """Close the transport."""
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()
        self._client = None
        self._connected = False

    @property
    def is_connected(self) -> bool:
        return self._connected


@dataclass
class V2ReplTransport:
    """V2 transport using WebSocket."""

    ws_url: str
    session_id: str
    access_token: str
    _ws: Any = field(default=None, init=False)
    _connected: bool = field(default=False, init=False)

    async def send(self, message: dict[str, Any]) -> None:
        """Send message via WebSocket."""
        if self._ws is None:
            extra_headers = {"Authorization": f"Bearer {self.access_token}"}
            self._ws = await websockets.connect(
                self.ws_url,
                additional_headers=extra_headers,
                max_size=None,
            )
            self._connected = True
        assert self._ws is not None
        await self._ws.send(json.dumps(message))

    async def receive(self) -> dict[str, Any]:
        """Receive message from WebSocket."""
        if self._ws is None:
            return {}
        raw = await self._ws.recv()
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8")
        try:
            parsed: Any = json.loads(raw)
        except json.JSONDecodeError:
            return {"raw": raw}
        return parsed if isinstance(parsed, dict) else {"data": parsed}

    async def close(self) -> None:
        """Close the WebSocket connection."""
        if self._ws is not None:
            await self._ws.close()
            self._ws = None
        self._connected = False

    @property
    def is_connected(self) -> bool:
        return self._connected


def create_v1_repl_transport(
    base_url: str,
    session_id: str,
    access_token: str,
) -> V1ReplTransport:
    """Create a V1 polling-based transport."""
    return V1ReplTransport(
        base_url=base_url,
        session_id=session_id,
        access_token=access_token,
    )


def create_v2_repl_transport(
    ws_url: str,
    session_id: str,
    access_token: str,
) -> V2ReplTransport:
    """Create a V2 WebSocket-based transport."""
    return V2ReplTransport(
        ws_url=ws_url,
        session_id=session_id,
        access_token=access_token,
    )
