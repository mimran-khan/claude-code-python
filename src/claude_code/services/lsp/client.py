"""
LSP client implementation.

Client for communicating with LSP servers.

Migrated from: services/lsp/LSPClient.ts (448 lines)
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import os
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ServerCapabilities:
    """LSP server capabilities."""

    text_document_sync: int | None = None
    completion_provider: bool = False
    hover_provider: bool = False
    definition_provider: bool = False
    references_provider: bool = False
    document_highlight_provider: bool = False
    document_symbol_provider: bool = False
    workspace_symbol_provider: bool = False
    code_action_provider: bool = False
    code_lens_provider: bool = False
    document_formatting_provider: bool = False
    document_range_formatting_provider: bool = False
    rename_provider: bool = False
    diagnostic_provider: bool = False


@dataclass
class InitializeResult:
    """Result of LSP initialization."""

    capabilities: ServerCapabilities = field(default_factory=ServerCapabilities)
    server_info: dict[str, str] | None = None


class LSPClient:
    """
    LSP client for communicating with language servers.

    Uses JSON-RPC over stdio.
    """

    def __init__(self, server_name: str, on_crash: Callable[[Exception], None] | None = None):
        self._server_name = server_name
        self._on_crash = on_crash
        self._process: asyncio.subprocess.Process | None = None
        self._capabilities: ServerCapabilities | None = None
        self._is_initialized = False
        self._is_stopping = False
        self._request_id = 0
        self._pending_requests: dict[int, asyncio.Future] = {}
        self._notification_handlers: dict[str, list[Callable]] = {}
        self._request_handlers: dict[str, Callable] = {}

    @property
    def capabilities(self) -> ServerCapabilities | None:
        return self._capabilities

    @property
    def is_initialized(self) -> bool:
        return self._is_initialized

    async def start(
        self,
        command: str,
        args: list[str],
        env: dict[str, str] | None = None,
        cwd: str | None = None,
    ) -> None:
        """
        Start the LSP server process.

        Args:
            command: Server command
            args: Command arguments
            env: Environment overrides
            cwd: Working directory
        """
        full_env = dict(os.environ)
        if env:
            full_env.update(env)

        self._process = await asyncio.create_subprocess_exec(
            command,
            *args,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=full_env,
            cwd=cwd,
        )

        # Start reading responses
        asyncio.create_task(self._read_messages())

    async def initialize(
        self,
        root_uri: str,
        capabilities: dict[str, Any] | None = None,
    ) -> InitializeResult:
        """
        Initialize the LSP server.

        Args:
            root_uri: Workspace root URI
            capabilities: Client capabilities

        Returns:
            InitializeResult
        """
        params = {
            "processId": os.getpid(),
            "rootUri": root_uri,
            "capabilities": capabilities or {},
        }

        result = await self.send_request("initialize", params)

        if result:
            caps_data = result.get("capabilities", {})
            self._capabilities = ServerCapabilities(
                completion_provider=bool(caps_data.get("completionProvider")),
                hover_provider=bool(caps_data.get("hoverProvider")),
                definition_provider=bool(caps_data.get("definitionProvider")),
                references_provider=bool(caps_data.get("referencesProvider")),
            )

        # Send initialized notification
        await self.send_notification("initialized", {})
        self._is_initialized = True

        return InitializeResult(capabilities=self._capabilities or ServerCapabilities())

    async def send_request(self, method: str, params: Any) -> Any:
        """
        Send a request to the server.

        Args:
            method: Request method
            params: Request parameters

        Returns:
            Response result
        """
        if not self._process or not self._process.stdin:
            raise RuntimeError("LSP server not started")

        self._request_id += 1
        request_id = self._request_id

        message = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
            "params": params,
        }

        future: asyncio.Future = asyncio.get_event_loop().create_future()
        self._pending_requests[request_id] = future

        await self._send_message(message)

        try:
            result = await asyncio.wait_for(future, timeout=30.0)
            return result
        except TimeoutError:
            del self._pending_requests[request_id]
            raise

    async def send_notification(self, method: str, params: Any) -> None:
        """
        Send a notification to the server.

        Args:
            method: Notification method
            params: Notification parameters
        """
        message = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
        }
        await self._send_message(message)

    def on_notification(self, method: str, handler: Callable[[Any], None]) -> None:
        """Register a notification handler."""
        if method not in self._notification_handlers:
            self._notification_handlers[method] = []
        self._notification_handlers[method].append(handler)

    def on_request(self, method: str, handler: Callable[[Any], Any]) -> None:
        """Register a request handler."""
        self._request_handlers[method] = handler

    async def stop(self) -> None:
        """Stop the LSP server."""
        self._is_stopping = True

        if self._process:
            try:
                await self.send_request("shutdown", None)
                await self.send_notification("exit", None)
            except Exception:
                pass

            self._process.terminate()
            try:
                await asyncio.wait_for(self._process.wait(), timeout=5.0)
            except TimeoutError:
                self._process.kill()

            self._process = None

        self._is_initialized = False

    async def _send_message(self, message: dict[str, Any]) -> None:
        """Send a JSON-RPC message."""
        if not self._process or not self._process.stdin:
            return

        content = json.dumps(message)
        header = f"Content-Length: {len(content)}\r\n\r\n"

        self._process.stdin.write(header.encode())
        self._process.stdin.write(content.encode())
        await self._process.stdin.drain()

    async def _read_messages(self) -> None:
        """Read messages from the server."""
        if not self._process or not self._process.stdout:
            return

        try:
            while True:
                # Read header
                header = b""
                while b"\r\n\r\n" not in header:
                    chunk = await self._process.stdout.read(1)
                    if not chunk:
                        return
                    header += chunk

                # Parse content length
                header_str = header.decode()
                content_length = 0
                for line in header_str.split("\r\n"):
                    if line.startswith("Content-Length:"):
                        content_length = int(line.split(":")[1].strip())
                        break

                if content_length == 0:
                    continue

                # Read content
                content = await self._process.stdout.read(content_length)
                message = json.loads(content.decode())

                await self._handle_message(message)

        except Exception as e:
            if not self._is_stopping and self._on_crash:
                self._on_crash(e)

    async def _handle_message(self, message: dict[str, Any]) -> None:
        """Handle an incoming message."""
        if "id" in message and "result" in message:
            # Response
            request_id = message["id"]
            if request_id in self._pending_requests:
                self._pending_requests[request_id].set_result(message.get("result"))
                del self._pending_requests[request_id]

        elif "id" in message and "error" in message:
            # Error response
            request_id = message["id"]
            if request_id in self._pending_requests:
                error = message["error"]
                self._pending_requests[request_id].set_exception(
                    RuntimeError(f"LSP error: {error.get('message', 'Unknown')}")
                )
                del self._pending_requests[request_id]

        elif "method" in message:
            method = message["method"]
            params = message.get("params")

            if "id" in message:
                # Request from server
                if method in self._request_handlers:
                    try:
                        result = self._request_handlers[method](params)
                        if asyncio.iscoroutine(result):
                            result = await result
                        await self._send_message(
                            {
                                "jsonrpc": "2.0",
                                "id": message["id"],
                                "result": result,
                            }
                        )
                    except Exception as e:
                        await self._send_message(
                            {
                                "jsonrpc": "2.0",
                                "id": message["id"],
                                "error": {"code": -32603, "message": str(e)},
                            }
                        )
            else:
                # Notification from server
                if method in self._notification_handlers:
                    for handler in self._notification_handlers[method]:
                        with contextlib.suppress(Exception):
                            handler(params)


def create_lsp_client(
    server_name: str,
    on_crash: Callable[[Exception], None] | None = None,
) -> LSPClient:
    """
    Create an LSP client.

    Args:
        server_name: Name of the server
        on_crash: Callback for server crashes

    Returns:
        LSPClient instance
    """
    return LSPClient(server_name, on_crash)
