"""Critical system constants and helpers."""

import os

from ..utils.debug import log_for_debugging

# System prompt prefixes
DEFAULT_PREFIX = "You are Claude Code, Anthropic's official CLI for Claude."
AGENT_SDK_CLAUDE_CODE_PRESET_PREFIX = (
    "You are Claude Code, Anthropic's official CLI for Claude, running within the Claude Agent SDK."
)
AGENT_SDK_PREFIX = "You are a Claude agent, built on Anthropic's Claude Agent SDK."

CLI_SYSPROMPT_PREFIX_VALUES = (
    DEFAULT_PREFIX,
    AGENT_SDK_CLAUDE_CODE_PRESET_PREFIX,
    AGENT_SDK_PREFIX,
)

# All possible CLI sysprompt prefix values
CLI_SYSPROMPT_PREFIXES = frozenset(CLI_SYSPROMPT_PREFIX_VALUES)


def get_cli_sysprompt_prefix(
    is_non_interactive: bool = False,
    has_append_system_prompt: bool = False,
) -> str:
    """Get the CLI system prompt prefix based on context."""
    # Note: In full migration, would check getAPIProvider() == "vertex"

    if is_non_interactive:
        if has_append_system_prompt:
            return AGENT_SDK_CLAUDE_CODE_PRESET_PREFIX
        return AGENT_SDK_PREFIX
    return DEFAULT_PREFIX


def _is_attribution_header_enabled() -> bool:
    """Check if attribution header is enabled."""
    env_val = os.environ.get("CLAUDE_CODE_ATTRIBUTION_HEADER", "")
    if env_val.lower() in ("0", "false", "no"):
        return False
    # Default to enabled
    return True


def get_attribution_header(fingerprint: str) -> str:
    """Get attribution header for API requests.

    Returns a header string with cc_version (including fingerprint) and cc_entrypoint.
    """
    if not _is_attribution_header_enabled():
        return ""

    version = os.environ.get("CLAUDE_CODE_VERSION", "0.0.0")
    full_version = f"{version}.{fingerprint}"
    entrypoint = os.environ.get("CLAUDE_CODE_ENTRYPOINT", "unknown")

    # cc_workload: turn-scoped hint for routing
    workload = os.environ.get("CLAUDE_CODE_WORKLOAD", "")
    workload_pair = f" cc_workload={workload};" if workload else ""

    header = f"x-anthropic-billing-header: cc_version={full_version}; cc_entrypoint={entrypoint};{workload_pair}"

    log_for_debugging(f"attribution header {header}")
    return header
