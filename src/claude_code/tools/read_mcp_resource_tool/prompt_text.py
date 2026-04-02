"""ReadMcpResource prompts."""

from __future__ import annotations

READ_MCP_RESOURCE_TOOL_NAME = "ReadMcpResourceTool"

DESCRIPTION = """
Reads a specific resource from an MCP server.
- server: The name of the MCP server to read from
- uri: The URI of the resource to read

Usage examples:
- Read a resource from a server: `readMcpResource({ server: "myserver", uri: "my-resource-uri" })`
""".strip()

PROMPT = """
Reads a specific resource from an MCP server, identified by server name and resource URI.

Parameters:
- server (required): The name of the MCP server from which to read the resource
- uri (required): The URI of the resource to read
""".strip()
