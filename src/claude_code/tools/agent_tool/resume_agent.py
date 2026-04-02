"""
Resume a previously spawned agent session.

Migrated from: tools/AgentTool/resumeAgent.ts

Orchestration is implemented in :mod:`claude_code.tools.agent_tool.run_agent` (`resume_agent`).
This module documents the TS split for agents that only import resume helpers.
"""

from __future__ import annotations

from .run_agent import resume_agent

__all__ = ["resume_agent"]
