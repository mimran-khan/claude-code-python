"""Agent summary generation for coordinator mode sub-agents.

Periodically generates progress summaries for background agents.
"""

import asyncio
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

SUMMARY_INTERVAL_MS = 30_000  # 30 seconds


@dataclass
class SummarizationHandle:
    """Handle for stopping summarization."""

    task: asyncio.Task | None = None
    stopped: bool = False


# Active summarization tasks
_active_summarizations: dict[str, SummarizationHandle] = {}


def build_summary_prompt(previous_summary: str | None) -> str:
    """Build the prompt for summary generation."""
    prev_line = ""
    if previous_summary:
        prev_line = f'\nPrevious: "{previous_summary}" — say something NEW.\n'

    return f"""Describe your most recent action in 3-5 words using present tense (-ing). Name the file or function, not the branch. Do not use tools.
{prev_line}
Good: "Reading runAgent.ts"
Good: "Fixing null check in validate.ts"
Good: "Running auth module tests"
Good: "Adding retry logic to fetchUser"

Bad (past tense): "Analyzed the branch diff"
Bad (too vague): "Investigating the issue"
Bad (too long): "Reviewing full branch diff and AgentTool.tsx integration"
Bad (branch name): "Analyzed adam/background-summary branch diff"""


def start_agent_summarization(
    task_id: str,
    agent_id: str,
    cache_safe_params: dict[str, Any],
    set_app_state: Callable[[Callable[[Any], Any]], None],
) -> dict[str, Any]:
    """Start periodic summarization for an agent.

    Returns a handle with a stop() function.
    """
    handle = SummarizationHandle()
    _active_summarizations[agent_id] = handle

    async def run_summarization_loop():

        while not handle.stopped:
            await asyncio.sleep(SUMMARY_INTERVAL_MS / 1000)

            if handle.stopped:
                break

            # In full implementation, would:
            # 1. Get agent transcript
            # 2. Run forked agent for summary
            # 3. Update AgentProgress with summary

            # Stub: just generate a placeholder summary
            f"Working on task {task_id[:8]}..."

    # Start the task
    handle.task = asyncio.create_task(run_summarization_loop())

    def stop():
        handle.stopped = True
        if handle.task:
            handle.task.cancel()
        _active_summarizations.pop(agent_id, None)

    return {"stop": stop}


def stop_agent_summarization(agent_id: str) -> None:
    """Stop summarization for an agent."""
    handle = _active_summarizations.get(agent_id)
    if handle:
        handle.stopped = True
        if handle.task:
            handle.task.cancel()
        _active_summarizations.pop(agent_id, None)


def get_agent_summary(agent_id: str) -> str | None:
    """Get the current summary for an agent."""
    # In full implementation, would read from AgentProgress
    return None
