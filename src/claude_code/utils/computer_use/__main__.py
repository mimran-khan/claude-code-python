"""``python -m claude_code.utils.computer_use`` → stdio MCP server."""

from __future__ import annotations

import asyncio

from .mcp_server import run_computer_use_mcp_server


def main() -> None:
    asyncio.run(run_computer_use_mcp_server())


if __name__ == "__main__":
    main()
