"""
Agent Tool Prompt.

Contains the tool name, description, and prompt generation functions.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..file_read.prompt import FILE_READ_TOOL_NAME
from ..file_write.prompt import FILE_WRITE_TOOL_NAME
from ..glob.prompt import GLOB_TOOL_NAME

AGENT_TOOL_NAME = "Task"


@dataclass
class AgentDefinition:
    """Definition of an agent type."""

    agent_type: str
    when_to_use: str
    tools: list[str] = field(default_factory=list)
    disallowed_tools: list[str] = field(default_factory=list)
    prompt: str = ""
    model: str | None = None


def get_tools_description(agent: AgentDefinition) -> str:
    """Get a description of tools available to an agent.

    Args:
        agent: The agent definition

    Returns:
        A string describing available tools
    """
    tools = agent.tools
    disallowed_tools = agent.disallowed_tools
    has_allowlist = bool(tools)
    has_denylist = bool(disallowed_tools)

    if has_allowlist and has_denylist:
        # Both defined: filter allowlist by denylist
        deny_set = set(disallowed_tools)
        effective_tools = [t for t in tools if t not in deny_set]
        if not effective_tools:
            return "None"
        return ", ".join(effective_tools)
    elif has_allowlist:
        return ", ".join(tools)
    elif has_denylist:
        return f"All tools except {', '.join(disallowed_tools)}"
    return "All tools"


def format_agent_line(agent: AgentDefinition) -> str:
    """Format one agent line for the agent listing.

    Args:
        agent: The agent definition

    Returns:
        Formatted string: "- type: whenToUse (Tools: ...)"
    """
    tools_description = get_tools_description(agent)
    return f"- {agent.agent_type}: {agent.when_to_use} (Tools: {tools_description})"


async def get_prompt(
    agent_definitions: list[AgentDefinition],
    is_coordinator: bool = False,
    allowed_agent_types: list[str] | None = None,
) -> str:
    """Get the full prompt for the agent tool.

    Args:
        agent_definitions: List of available agent definitions
        is_coordinator: Whether this is being called from coordinator mode
        allowed_agent_types: Optional list of allowed agent types

    Returns:
        The formatted prompt string
    """
    # Filter agents by allowed types
    if allowed_agent_types:
        effective_agents = [a for a in agent_definitions if a.agent_type in allowed_agent_types]
    else:
        effective_agents = agent_definitions

    agent_list_section = f"""Available agent types and the tools they have access to:
{chr(10).join(format_agent_line(agent) for agent in effective_agents)}"""

    shared = f"""Launch a new agent to handle complex, multi-step tasks autonomously.

The {AGENT_TOOL_NAME} tool launches specialized agents (subprocesses) that autonomously handle complex tasks. Each agent type has specific capabilities and tools available to it.

{agent_list_section}

When using the {AGENT_TOOL_NAME} tool, specify a subagent_type parameter to select which agent type to use. If omitted, the general-purpose agent is used."""

    if is_coordinator:
        return shared

    when_not_to_use = f"""
When NOT to use the {AGENT_TOOL_NAME} tool:
- If you want to read a specific file path, use the {FILE_READ_TOOL_NAME} tool or the {GLOB_TOOL_NAME} tool instead of the {AGENT_TOOL_NAME} tool, to find the match more quickly
- If you are searching for a specific class definition like "class Foo", use the {GLOB_TOOL_NAME} tool instead, to find the match more quickly
- If you are searching for code within a specific file or set of 2-3 files, use the {FILE_READ_TOOL_NAME} tool instead of the {AGENT_TOOL_NAME} tool, to find the match more quickly
- Other tasks that are not related to the agent descriptions above
"""

    writing_prompt_section = """
## Writing the prompt

Brief the agent like a smart colleague who just walked into the room — it hasn't seen this conversation, doesn't know what you've tried, doesn't understand why this task matters.
- Explain what you're trying to accomplish and why.
- Describe what you've already learned or ruled out.
- Give enough context about the surrounding problem that the agent can make judgment calls rather than just following a narrow instruction.
- If you need a short response, say so ("report in under 200 words").
- Lookups: hand over the exact command. Investigations: hand over the question — prescribed steps become dead weight when the premise is wrong.

Terse command-style prompts produce shallow, generic work.

**Never delegate understanding.** Don't write "based on your findings, fix the bug" or "based on the research, implement it." Those phrases push synthesis onto the agent instead of doing it yourself. Write prompts that prove you understood: include file paths, line numbers, what specifically to change.
"""

    examples = f"""Example usage:

<example_agent_descriptions>
"test-runner": use this agent after you are done writing code to run tests
"greeting-responder": use this agent to respond to user greetings with a friendly joke
</example_agent_descriptions>

<example>
user: "Please write a function that checks if a number is prime"
assistant: I'm going to use the {FILE_WRITE_TOOL_NAME} tool to write the following code:
<code>
function isPrime(n) {{
  if (n <= 1) return false
  for (let i = 2; i * i <= n; i++) {{
    if (n % i === 0) return false
  }}
  return true
}}
</code>
<commentary>
Since a significant piece of code was written and the task was completed, now use the test-runner agent to run the tests
</commentary>
assistant: Uses the {AGENT_TOOL_NAME} tool to launch the test-runner agent
</example>

<example>
user: "Hello"
<commentary>
Since the user is greeting, use the greeting-responder agent to respond with a friendly joke
</commentary>
assistant: "I'm going to use the {AGENT_TOOL_NAME} tool to launch the greeting-responder agent"
</example>
"""

    return f"""{shared}
{when_not_to_use}

Usage notes:
- Always include a short description (3-5 words) summarizing what the agent will do
- When the agent is done, it will return a single message back to you. The result returned by the agent is not visible to the user. To show the user the result, you should send a text message back to the user with a concise summary of the result.
- Each Agent invocation starts fresh — provide a complete task description.
- The agent's outputs should generally be trusted
- Clearly tell the agent whether you expect it to write code or just to do research (search, file reads, web fetches, etc.), since it is not aware of the user's intent
- If the agent description mentions that it should be used proactively, then you should try your best to use it without the user having to ask for it first. Use your judgement.
- If the user specifies that they want you to run agents "in parallel", you MUST send a single message with multiple {AGENT_TOOL_NAME} tool use content blocks. For example, if you need to launch both a build-validator agent and a test-runner agent in parallel, send a single message with both tool calls.
- You can optionally set `isolation: "worktree"` to run the agent in a temporary git worktree, giving it an isolated copy of the repository. The worktree is automatically cleaned up if the agent makes no changes; if changes are made, the worktree path and branch are returned in the result.{writing_prompt_section}

{examples}"""
