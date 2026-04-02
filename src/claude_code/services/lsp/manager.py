"""
LSP server manager.

Manage multiple LSP server instances.

Migrated from: services/lsp/LSPServerManager.ts + manager.ts
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .client import LSPClient, create_lsp_client


@dataclass
class LSPServerConfig:
    """Configuration for an LSP server."""

    name: str
    command: str
    args: list[str] = field(default_factory=list)
    file_patterns: list[str] = field(default_factory=list)
    root_uri: str | None = None
    env: dict[str, str] = field(default_factory=dict)


@dataclass
class LSPServerInstance:
    """A running LSP server instance."""

    config: LSPServerConfig
    client: LSPClient
    is_running: bool = False
    start_time: float | None = None


class LSPServerManager:
    """
    Manager for LSP servers.

    Handles starting, stopping, and routing requests to appropriate servers.
    """

    def __init__(self):
        self._servers: dict[str, LSPServerInstance] = {}
        self._configs: dict[str, LSPServerConfig] = {}

    def register_server(self, config: LSPServerConfig) -> None:
        """
        Register an LSP server configuration.

        Args:
            config: Server configuration
        """
        self._configs[config.name] = config

    async def start_server(self, name: str, root_uri: str | None = None) -> LSPClient:
        """
        Start an LSP server.

        Args:
            name: Server name
            root_uri: Workspace root URI

        Returns:
            LSPClient for the server
        """
        if name in self._servers and self._servers[name].is_running:
            return self._servers[name].client

        config = self._configs.get(name)
        if not config:
            raise ValueError(f"Unknown LSP server: {name}")

        def on_crash(error: Exception) -> None:
            if name in self._servers:
                self._servers[name].is_running = False

        client = create_lsp_client(name, on_crash)

        await client.start(
            config.command,
            config.args,
            env=config.env,
        )

        uri = root_uri or config.root_uri or "file:///"
        await client.initialize(uri)

        import time

        instance = LSPServerInstance(
            config=config,
            client=client,
            is_running=True,
            start_time=time.time(),
        )

        self._servers[name] = instance
        return client

    async def stop_server(self, name: str) -> None:
        """
        Stop an LSP server.

        Args:
            name: Server name
        """
        if name not in self._servers:
            return

        instance = self._servers[name]
        if instance.is_running:
            await instance.client.stop()
            instance.is_running = False

    async def stop_all(self) -> None:
        """Stop all running servers."""
        for name in list(self._servers.keys()):
            await self.stop_server(name)

    def get_server(self, name: str) -> LSPClient | None:
        """
        Get a running server client.

        Args:
            name: Server name

        Returns:
            LSPClient or None
        """
        instance = self._servers.get(name)
        if instance and instance.is_running:
            return instance.client
        return None

    def get_server_for_file(self, file_path: str) -> LSPClient | None:
        """
        Get the appropriate server for a file.

        Args:
            file_path: Path to file

        Returns:
            LSPClient or None
        """
        import fnmatch

        for instance in self._servers.values():
            if not instance.is_running:
                continue

            for pattern in instance.config.file_patterns:
                if fnmatch.fnmatch(file_path, pattern):
                    return instance.client

        return None

    def list_servers(self) -> list[str]:
        """List registered server names."""
        return list(self._configs.keys())

    def list_running_servers(self) -> list[str]:
        """List running server names."""
        return [name for name, instance in self._servers.items() if instance.is_running]


# Global manager instance
_manager: LSPServerManager | None = None


def get_lsp_manager() -> LSPServerManager:
    """Get the global LSP manager."""
    global _manager
    if _manager is None:
        _manager = LSPServerManager()
    return _manager


async def start_lsp_server(
    name: str,
    root_uri: str | None = None,
) -> LSPClient:
    """Start an LSP server."""
    return await get_lsp_manager().start_server(name, root_uri)


async def stop_lsp_server(name: str) -> None:
    """Stop an LSP server."""
    await get_lsp_manager().stop_server(name)
