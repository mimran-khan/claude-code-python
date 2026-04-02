"""
MCP command.

Manage MCP servers.

Migrated from: commands/mcp/index.ts
"""

from __future__ import annotations

from ...services.mcp.config import get_mcp_servers
from ..base import Command, CommandContext, CommandResult


def _serialize_mcp_entry(name: str, cfg: object) -> dict[str, object]:
    transport = getattr(cfg, "type", "unknown")
    entry: dict[str, object] = {"name": name, "transport": transport}
    url = getattr(cfg, "url", None)
    if isinstance(url, str) and url:
        entry["url"] = url
    cmd = getattr(cfg, "command", None)
    if isinstance(cmd, str) and cmd:
        entry["command"] = cmd
    return entry


class MCPCommand(Command):
    """Manage MCP servers."""

    @property
    def name(self) -> str:
        return "mcp"

    @property
    def description(self) -> str:
        return "Manage MCP (Model Context Protocol) servers"

    async def execute(self, context: CommandContext) -> CommandResult:
        """Manage MCP servers."""
        args = context.args

        if not args:
            return CommandResult(
                success=True,
                message="MCP Commands: list, add, remove, status",
                output={"action": "showMCPHelp"},
            )

        subcommand = args[0]

        if subcommand == "list":
            servers = get_mcp_servers()
            if not servers:
                return CommandResult(
                    success=True,
                    output={"servers": [], "message": "No MCP servers configured."},
                )
            rows = [_serialize_mcp_entry(n, c) for n, c in servers.items()]
            return CommandResult(
                success=True,
                output={
                    "servers": rows,
                    "message": f"{len(rows)} MCP server(s) configured.",
                },
            )

        elif subcommand == "add":
            if len(args) < 2:
                return CommandResult(
                    success=False,
                    error="Usage: /mcp add <server-name> [options]",
                )
            server_name = args[1]
            return CommandResult(
                success=True,
                message=f"Adding MCP server: {server_name}",
                output={"action": "addMCP", "serverName": server_name},
            )

        elif subcommand == "remove":
            if len(args) < 2:
                return CommandResult(
                    success=False,
                    error="Usage: /mcp remove <server-name>",
                )
            server_name = args[1]
            return CommandResult(
                success=True,
                message=f"Removing MCP server: {server_name}",
            )

        elif subcommand == "status":
            servers = get_mcp_servers()
            if not servers:
                return CommandResult(
                    success=True,
                    output={"servers": [], "message": "No MCP servers configured."},
                )
            rows = [
                {**_serialize_mcp_entry(n, c), "runtime": "not_tracked"}
                for n, c in servers.items()
            ]
            return CommandResult(
                success=True,
                output={
                    "servers": rows,
                    "message": f"{len(rows)} configured; process/runtime state is not tracked by this CLI.",
                },
            )

        return CommandResult(
            success=False,
            error=f"Unknown subcommand: {subcommand}",
        )
