"""
Brief Tool Prompt.
"""

from __future__ import annotations

BRIEF_TOOL_NAME = "Brief"
LEGACY_BRIEF_TOOL_NAME = "Kairos"

DESCRIPTION = "Send a message to the user"

BRIEF_TOOL_PROMPT = """Send a message to the user.

Use this tool when you need to communicate with the user directly. The message
supports markdown formatting.

## When to Use

- To provide status updates on long-running tasks
- To ask clarifying questions
- To report completion of requested work
- To surface important information proactively

## Attachments

You can attach files (photos, screenshots, diffs, logs) that the user should
see alongside your message. Use absolute or relative paths.

## Status

- `normal`: Use when replying to something the user just said
- `proactive`: Use when surfacing something the user hasn't asked for and needs
  to see now (task completion while they're away, a blocker you hit, an
  unsolicited status update)
"""
