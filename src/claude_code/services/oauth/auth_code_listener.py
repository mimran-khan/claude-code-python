"""
Localhost HTTP server to capture OAuth redirect (authorization code).

Migrated from: services/oauth/auth-code-listener.ts
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from urllib.parse import parse_qs, urlparse

from ...constants.oauth import get_oauth_config
from ...utils.log import log_error
from ..analytics.index import log_event
from .client import should_use_claude_ai_auth


class AuthCodeListener:
    """Asyncio TCP server for /callback OAuth redirects."""

    def __init__(self, callback_path: str = "/callback") -> None:
        self._callback_path = callback_path
        self._server: asyncio.AbstractServer | None = None
        self._port: int = 0
        self._resolver: asyncio.Future[str] | None = None
        self._rejecter: asyncio.Future[None] | None = None
        self._expected_state: str | None = None
        self._pending_writer: asyncio.StreamWriter | None = None

    async def start(self, port: int | None = None) -> int:
        self._server = await asyncio.start_server(
            self._handle_client,
            host="127.0.0.1",
            port=0 if port is None else port,
        )
        sockets = self._server.sockets
        if not sockets:
            raise RuntimeError("OAuth callback server has no sockets")
        self._port = sockets[0].getsockname()[1]
        return self._port

    @property
    def port(self) -> int:
        return self._port

    def has_pending_response(self) -> bool:
        return self._pending_writer is not None

    async def wait_for_authorization(
        self,
        state: str,
        on_ready: Callable[[], Awaitable[None]],
    ) -> str:
        loop = asyncio.get_event_loop()
        self._resolver = loop.create_future()
        self._rejecter = loop.create_future()
        self._expected_state = state
        await on_ready()
        return await asyncio.wait_for(self._resolver, timeout=None)

    def handle_success_redirect(self, scopes: list[str]) -> None:
        if self._pending_writer is None:
            return
        cfg = get_oauth_config()
        success_url = cfg.CLAUDEAI_SUCCESS_URL if should_use_claude_ai_auth(scopes) else cfg.CONSOLE_SUCCESS_URL
        body = b"Redirecting...\n"
        response = (
            f"HTTP/1.1 302 Found\r\nLocation: {success_url}\r\nContent-Length: {len(body)}\r\nConnection: close\r\n\r\n"
        ).encode()
        try:
            self._pending_writer.write(response + body)
        finally:
            self._pending_writer.close()
            self._pending_writer = None
        log_event("tengu_oauth_automatic_redirect", {})

    def handle_error_redirect(self) -> None:
        if self._pending_writer is None:
            return
        error_url = get_oauth_config().CLAUDEAI_SUCCESS_URL
        body = b"Redirecting...\n"
        response = (
            f"HTTP/1.1 302 Found\r\nLocation: {error_url}\r\nContent-Length: {len(body)}\r\nConnection: close\r\n\r\n"
        ).encode()
        try:
            self._pending_writer.write(response + body)
        finally:
            self._pending_writer.close()
            self._pending_writer = None
        log_event("tengu_oauth_automatic_redirect_error", {})

    async def _handle_client(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        try:
            request_line = await reader.readline()
            if not request_line:
                writer.close()
                await writer.wait_closed()
                return
            # Read headers until blank line
            while True:
                line = await reader.readline()
                if line in (b"\r\n", b"\n", b""):
                    break
            parts = request_line.decode("utf-8", errors="replace").strip().split()
            if len(parts) < 2:
                writer.write(b"HTTP/1.1 400 Bad Request\r\n\r\n")
                writer.close()
                await writer.wait_closed()
                return
            path_with_query = parts[1]
            parsed = urlparse(path_with_query)
            if parsed.path != self._callback_path:
                writer.write(b"HTTP/1.1 404 Not Found\r\n\r\n")
                writer.close()
                await writer.wait_closed()
                return
            qs = parse_qs(parsed.query)
            code = (qs.get("code") or [None])[0]
            st = (qs.get("state") or [None])[0]
            if not code:
                writer.write(b"HTTP/1.1 400 Bad Request\r\n\r\nAuthorization code not found")
                writer.close()
                await writer.wait_closed()
                self._reject(RuntimeError("No authorization code received"))
                return
            if st != self._expected_state:
                writer.write(b"HTTP/1.1 400 Bad Request\r\n\r\nInvalid state parameter")
                writer.close()
                await writer.wait_closed()
                self._reject(RuntimeError("Invalid state parameter"))
                return
            self._pending_writer = writer
            if self._resolver and not self._resolver.done():
                self._resolver.set_result(code)
        except Exception as err:
            log_error(err if isinstance(err, Exception) else RuntimeError(str(err)))
            self._reject(err if isinstance(err, BaseException) else RuntimeError(str(err)))
            try:
                writer.close()
                await writer.wait_closed()
            except Exception:
                pass

    def _reject(self, err: BaseException) -> None:
        if self._rejecter and not self._rejecter.done():
            self._rejecter.set_exception(err)
        if self._resolver and not self._resolver.done():
            self._resolver.cancel()

    def close(self) -> None:
        if self._pending_writer:
            self.handle_error_redirect()
        if self._server:
            self._server.close()
        self._server = None
