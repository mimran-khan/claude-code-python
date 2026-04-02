"""Prompt strings for ReadMcpResource tool.

Migrated from: tools/ReadMcpResourceTool/prompt.ts
"""

READ_MCP_RESOURCE_TOOL_NAME = "ReadMcpResourceTool"

DESCRIPTION = """
Reads a specific resource from an MCP server.
- server: The name of the MCP server to read from
- uri: The URI of the resource to read
"""

PROMPT = """
Reads a specific resource from an MCP server, identified by server name and resource URI.

Parameters:
- server (required): The name of the MCP server from which to read the resource
- uri (required): The URI of the resource to read
"""
