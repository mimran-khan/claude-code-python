"""
JSON-RPC transports for MCP (stdio and SSE).

Stdio: line-delimited JSON-RPC over subprocess stdin/stdout.
SSE: GET stream for server messages + POST to session endpoint (MCP SSE transport).
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import logging
from dataclasses import dataclass
from typing import Any, Protocol
from urllib.parse import urljoin, urlparse

import httpx

from .types import McpSSEServerConfig, McpStdioServerConfig

logger = logging.getLogger(__name__)


@dataclass
class JsonRpcResponse:
    """Parsed JSON-RPC 2.0 response."""

    jsonrpc: str
    id: int | str | None
    result: Any
    error: dict[str, Any] | None


class McpJsonRpcTransport(Protocol):
    """Transport that can send JSON-RPC requests and return responses."""

    async def connect(self) -> None:
        """Establish transport (subprocess or SSE session)."""
        ...

    async def send_request(self, method: str, params: dict[str, Any]) -> JsonRpcResponse | None:
        """Send a request and wait for the matching response."""
        ...

    async def send_notification(self, method: str, params: dict[str, Any]) -> None:
        """Fire-and-forget notification (no response)."""
        ...

    async def aclose(self) -> None:
        """Release resources."""
        ...


def _parse_jsonrpc_line(raw: bytes) -> dict[str, Any] | None:
    line = raw.decode(errors="replace").strip()
    if not line:
        return None
    try:
        return json.loads(line)
    except json.JSONDecodeError:
        logger.warning("mcp_invalid_json_line", extra={"preview": line[:200]})
        return None


class StdioJsonRpcTransport:
    """MCP over subprocess stdio (newline-delimited JSON-RPC)."""

    def __init__(self, config: McpStdioServerConfig) -> None:
        self._config = config
        self._process: asyncio.subprocess.Process | None = None
        self._reader_task: asyncio.Task[None] | None = None
        self._pending: dict[int | str, asyncio.Future[dict[str, Any]]] = {}
        self._next_id = 0
        self._closed = asyncio.Event()

    async def connect(self) -> None:
        if self._process is not None:
            return
        self._closed.clear()
        self._process = await asyncio.create_subprocess_exec(
            self._config.command,
            *self._config.args,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env={**self._config.env} if self._config.env else None,
        )
        if not self._process.stdin or not self._process.stdout:
            raise RuntimeError("stdio pipes unavailable")
        self._reader_task = asyncio.create_task(self._read_stdout_loop())

    async def _read_stdout_loop(self) -> None:
        assert self._process and self._process.stdout
        try:
            while not self._closed.is_set():
                line = await self._process.stdout.readline()
                if not line:
                    break
                data = _parse_jsonrpc_line(line)
                if data is None:
                    continue
                # Notifications have no id
                if "id" not in data or data["id"] is None:
                    continue
                req_id = data["id"]
                fut = self._pending.pop(req_id, None)
                if fut and not fut.done():
                    fut.set_result(data)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            for fut in self._pending.values():
                if not fut.done():
                    fut.set_exception(exc)
            self._pending.clear()
        finally:
            for fut in tuple(self._pending.values()):
                if not fut.done():
                    fut.set_exception(RuntimeError("MCP stdio reader ended"))
            self._pending.clear()

    def _alloc_id(self) -> int:
        self._next_id += 1
        return self._next_id

    async def send_request(self, method: str, params: dict[str, Any]) -> JsonRpcResponse | None:
        if not self._process or not self._process.stdin:
            return None
        req_id = self._alloc_id()
        fut: asyncio.Future[dict[str, Any]] = asyncio.get_running_loop().create_future()
        self._pending[req_id] = fut
        payload = {
            "jsonrpc": "2.0",
            "id": req_id,
            "method": method,
            "params": params,
        }
        line = json.dumps(payload) + "\n"
        self._process.stdin.write(line.encode())
        await self._process.stdin.drain()
        try:
            data = await asyncio.wait_for(fut, timeout=120.0)
        except TimeoutError:
            self._pending.pop(req_id, None)
            return JsonRpcResponse(jsonrpc="2.0", id=req_id, result=None, error={"message": "timeout"})
        return JsonRpcResponse(
            jsonrpc=data.get("jsonrpc", "2.0"),
            id=data.get("id"),
            result=data.get("result"),
            error=data.get("error"),
        )

    async def send_notification(self, method: str, params: dict[str, Any]) -> None:
        if not self._process or not self._process.stdin:
            return
        payload = {"jsonrpc": "2.0", "method": method, "params": params}
        line = json.dumps(payload) + "\n"
        self._process.stdin.write(line.encode())
        await self._process.stdin.drain()

    async def aclose(self) -> None:
        self._closed.set()
        if self._reader_task:
            self._reader_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._reader_task
            self._reader_task = None
        if self._process:
            self._process.terminate()
            try:
                await asyncio.wait_for(self._process.wait(), timeout=5.0)
            except TimeoutError:
                self._process.kill()
            self._process = None


class SseJsonRpcTransport:
    """
    MCP SSE transport: GET ``url`` for events; first ``endpoint`` event gives POST URL;
    JSON-RPC responses arrive as SSE ``message`` events.
    """

    def __init__(self, config: McpSSEServerConfig) -> None:
        self._config = config
        self._client: httpx.AsyncClient | None = None
        self._post_url: str | None = None
        self._endpoint_event = asyncio.Event()
        self._sse_task: asyncio.Task[None] | None = None
        self._pending: dict[int | str, asyncio.Future[dict[str, Any]]] = {}
        self._next_id = 0
        self._stop = asyncio.Event()

    def _alloc_id(self) -> int:
        self._next_id += 1
        return self._next_id

    async def connect(self) -> None:
        if self._client is not None:
            return
        try:
            from httpx_sse import aconnect_sse
        except ImportError as e:
            raise RuntimeError("SSE transport requires the httpx-sse package (install mcp or httpx-sse)") from e

        headers = dict(self._config.headers)
        timeout = httpx.Timeout(30.0, read=300.0)
        self._client = httpx.AsyncClient(headers=headers, timeout=timeout)
        self._stop.clear()
        self._sse_task = asyncio.create_task(self._sse_loop(aconnect_sse))
        await asyncio.wait_for(self._endpoint_event.wait(), timeout=60.0)
        if not self._post_url:
            raise RuntimeError("MCP SSE: no endpoint event received")

    async def _sse_loop(self, aconnect_sse: Any) -> None:
        assert self._client is not None
        url = self._config.url
        try:
            async with aconnect_sse(self._client, "GET", url) as event_source:
                event_source.response.raise_for_status()
                async for sse in event_source.aiter_sse():
                    if self._stop.is_set():
                        break
                    if sse.event == "endpoint":
                        endpoint_url = urljoin(url, sse.data)
                        url_parsed = urlparse(url)
                        ep_parsed = urlparse(endpoint_url)
                        if url_parsed.netloc != ep_parsed.netloc or url_parsed.scheme != ep_parsed.scheme:
                            raise ValueError(f"SSE endpoint origin mismatch: {endpoint_url}")
                        self._post_url = endpoint_url
                        self._endpoint_event.set()
                    elif sse.event == "message":
                        if not sse.data:
                            continue
                        try:
                            data = json.loads(sse.data)
                        except json.JSONDecodeError:
                            logger.warning("mcp_sse_bad_message", extra={"preview": sse.data[:200]})
                            continue
                        if "id" not in data or data["id"] is None:
                            continue
                        req_id = data["id"]
                        fut = self._pending.pop(req_id, None)
                        if fut and not fut.done():
                            fut.set_result(data)
                    else:
                        logger.debug("mcp_sse_unknown_event", extra={"event": sse.event})
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            for fut in self._pending.values():
                if not fut.done():
                    fut.set_exception(exc)
            self._pending.clear()
            if not self._endpoint_event.is_set():
                self._endpoint_event.set()
        finally:
            for fut in tuple(self._pending.values()):
                if not fut.done():
                    fut.set_exception(RuntimeError("MCP SSE connection closed"))
            self._pending.clear()

    async def send_request(self, method: str, params: dict[str, Any]) -> JsonRpcResponse | None:
        if not self._client or not self._post_url:
            return None
        req_id = self._alloc_id()
        fut: asyncio.Future[dict[str, Any]] = asyncio.get_running_loop().create_future()
        self._pending[req_id] = fut
        body = {
            "jsonrpc": "2.0",
            "id": req_id,
            "method": method,
            "params": params,
        }
        try:
            r = await self._client.post(self._post_url, json=body)
            r.raise_for_status()
        except Exception as exc:
            self._pending.pop(req_id, None)
            if not fut.done():
                fut.set_exception(exc)
            return JsonRpcResponse(jsonrpc="2.0", id=req_id, result=None, error={"message": str(exc)})
        try:
            data = await asyncio.wait_for(fut, timeout=120.0)
        except TimeoutError:
            self._pending.pop(req_id, None)
            return JsonRpcResponse(jsonrpc="2.0", id=req_id, result=None, error={"message": "timeout"})
        return JsonRpcResponse(
            jsonrpc=data.get("jsonrpc", "2.0"),
            id=data.get("id"),
            result=data.get("result"),
            error=data.get("error"),
        )

    async def send_notification(self, method: str, params: dict[str, Any]) -> None:
        if not self._client or not self._post_url:
            return
        body = {"jsonrpc": "2.0", "method": method, "params": params}
        r = await self._client.post(self._post_url, json=body)
        r.raise_for_status()

    async def aclose(self) -> None:
        self._stop.set()
        if self._sse_task:
            self._sse_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._sse_task
            self._sse_task = None
        if self._client:
            await self._client.aclose()
            self._client = None
        self._post_url = None
        self._endpoint_event = asyncio.Event()
