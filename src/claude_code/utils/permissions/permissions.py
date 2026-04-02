"""
Core permissions module.

Main permission checking and rule matching logic.

Migrated from: utils/permissions/permissions.ts (1487 lines) - Core logic
"""

from __future__ import annotations

from typing import Any

from .permission_mode import permission_mode_title
from .permission_result import (
    PermissionAllowDecision,
    PermissionAskDecision,
    PermissionDenyDecision,
    PermissionResult,
)
from .permission_rule import (
    PermissionRule,
    PermissionRuleSource,
    PermissionRuleValue,
)
from .rule_parser import (
    permission_rule_value_from_string,
    permission_rule_value_to_string,
)

# Permission rule sources in priority order
PERMISSION_RULE_SOURCES: list[PermissionRuleSource] = [
    "policySettings",
    "flagSettings",
    "userSettings",
    "projectSettings",
    "localSettings",
    "cliArg",
    "command",
    "session",
]


def permission_rule_source_display_string(source: PermissionRuleSource) -> str:
    """Get display name for a permission rule source."""
    display_names = {
        "policySettings": "managed settings",
        "flagSettings": "feature flag settings",
        "userSettings": "user settings",
        "projectSettings": "project settings",
        "localSettings": "local settings",
        "cliArg": "CLI argument",
        "command": "command",
        "session": "session",
    }
    return display_names.get(source, source)


def get_allow_rules(
    always_allow_rules: dict[str, list[str]],
) -> list[PermissionRule]:
    """Get all allow rules from a permission context."""
    rules = []
    for source in PERMISSION_RULE_SOURCES:
        rule_strings = always_allow_rules.get(source, [])
        for rule_string in rule_strings:
            rules.append(
                PermissionRule(
                    source=source,  # type: ignore
                    rule_behavior="allow",
                    rule_value=permission_rule_value_from_string(rule_string),
                )
            )
    return rules


def get_deny_rules(
    always_deny_rules: dict[str, list[str]],
) -> list[PermissionRule]:
    """Get all deny rules from a permission context."""
    rules = []
    for source in PERMISSION_RULE_SOURCES:
        rule_strings = always_deny_rules.get(source, [])
        for rule_string in rule_strings:
            rules.append(
                PermissionRule(
                    source=source,  # type: ignore
                    rule_behavior="deny",
                    rule_value=permission_rule_value_from_string(rule_string),
                )
            )
    return rules


def get_ask_rules(
    always_ask_rules: dict[str, list[str]],
) -> list[PermissionRule]:
    """Get all ask rules from a permission context."""
    rules = []
    for source in PERMISSION_RULE_SOURCES:
        rule_strings = always_ask_rules.get(source, [])
        for rule_string in rule_strings:
            rules.append(
                PermissionRule(
                    source=source,  # type: ignore
                    rule_behavior="ask",
                    rule_value=permission_rule_value_from_string(rule_string),
                )
            )
    return rules


def tool_matches_rule(
    tool_name: str,
    rule: PermissionRule,
    mcp_info: dict[str, Any] | None = None,
) -> bool:
    """
    Check if the entire tool matches a rule.

    This matches "Bash" but not "Bash(prefix:*)" for BashTool.
    Also matches MCP tools with a server name.
    """
    # Rule must not have content to match the entire tool
    if rule.rule_value.rule_content is not None:
        return False

    # Check for exact name match
    if rule.rule_value.tool_name == tool_name:
        return True

    # MCP tools matching
    if mcp_info:
        server_name = mcp_info.get("server_name", "")
        mcp_tool_name = f"mcp__{server_name}"
        if rule.rule_value.tool_name == mcp_tool_name:
            return True

    return False


def get_rule_by_contents_for_tool_name(
    rule_content: str,
    tool_name: str,
) -> PermissionRuleValue:
    """Create a rule value with content for a specific tool."""
    return PermissionRuleValue(
        tool_name=tool_name,
        rule_content=rule_content,
    )


def create_permission_request_message(
    tool_name: str,
    decision_reason: dict[str, Any] | None = None,
) -> str:
    """Create a permission request message explaining the request."""
    if decision_reason:
        reason_type = decision_reason.get("type", "")

        if reason_type == "classifier":
            classifier = decision_reason.get("classifier", "")
            reason = decision_reason.get("reason", "")
            return f"Classifier '{classifier}' requires approval for this {tool_name} command: {reason}"

        if reason_type == "hook":
            hook_name = decision_reason.get("hook_name", "")
            reason = decision_reason.get("reason", "")
            if reason:
                return f"Hook '{hook_name}' blocked this action: {reason}"
            return f"Hook '{hook_name}' requires approval for this {tool_name} command"

        if reason_type == "rule":
            rule = decision_reason.get("rule")
            if rule:
                rule_string = permission_rule_value_to_string(rule.rule_value)
                source_string = permission_rule_source_display_string(rule.source)
                return f"Permission rule '{rule_string}' from {source_string} requires approval for this {tool_name} command"

        if reason_type == "subcommandResults":
            reasons = decision_reason.get("reasons", [])
            needs_approval = []
            for cmd, result in reasons:
                if result.get("behavior") in ("ask", "passthrough"):
                    needs_approval.append(cmd)

            if needs_approval:
                n = len(needs_approval)
                parts = "part" if n == 1 else "parts"
                requires = "requires" if n == 1 else "require"
                return f"This {tool_name} command contains multiple operations. The following {parts} {requires} approval: {', '.join(needs_approval)}"
            return f"This {tool_name} command contains multiple operations that require approval"

        if reason_type == "permissionPromptTool":
            prompt_tool_name = decision_reason.get("permission_prompt_tool_name", "")
            return f"Tool '{prompt_tool_name}' requires approval for this {tool_name} command"

        if reason_type == "sandboxOverride":
            return "Run outside of the sandbox"

        if reason_type == "workingDir":
            return decision_reason.get("reason", "")

        if reason_type in ("safetyCheck", "other"):
            return decision_reason.get("reason", "")

        if reason_type == "mode":
            mode = decision_reason.get("mode", "")
            mode_title = permission_mode_title(mode)
            return f"Current permission mode ({mode_title}) requires approval for this {tool_name} command"

        if reason_type == "asyncAgent":
            return decision_reason.get("reason", "")

    # Default message
    return f"Claude requested permissions to use {tool_name}, but you haven't granted it yet."


def check_tool_permission(
    tool_name: str,
    tool_input: dict[str, Any],
    allow_rules: list[PermissionRule],
    deny_rules: list[PermissionRule],
    ask_rules: list[PermissionRule],
    mcp_info: dict[str, Any] | None = None,
) -> PermissionResult:
    """
    Check permissions for a tool invocation.

    Returns a PermissionResult indicating whether the action is
    allowed, denied, or requires user confirmation.
    """
    # Check deny rules first (highest priority)
    for rule in deny_rules:
        if _rule_matches_tool_input(tool_name, tool_input, rule, mcp_info):
            return PermissionResult(
                behavior="deny",
                decision=PermissionDenyDecision(
                    reason=f"Denied by rule: {permission_rule_value_to_string(rule.rule_value)}",
                    decision_reason={"type": "rule", "rule": rule},
                ),
                tool_name=tool_name,
                tool_input=tool_input,
            )

    # Check ask rules next
    for rule in ask_rules:
        if _rule_matches_tool_input(tool_name, tool_input, rule, mcp_info):
            return PermissionResult(
                behavior="ask",
                decision=PermissionAskDecision(
                    source_input=tool_input,
                    decision_reason={"type": "rule", "rule": rule},
                ),
                tool_name=tool_name,
                tool_input=tool_input,
            )

    # Check allow rules
    for rule in allow_rules:
        if _rule_matches_tool_input(tool_name, tool_input, rule, mcp_info):
            return PermissionResult(
                behavior="allow",
                decision=PermissionAllowDecision(
                    updated_input=tool_input,
                    decision_reason={"type": "rule", "rule": rule},
                ),
                tool_name=tool_name,
                tool_input=tool_input,
            )

    # Default: ask for permission
    return PermissionResult(
        behavior="ask",
        decision=PermissionAskDecision(
            source_input=tool_input,
            decision_reason={"type": "other", "reason": "No matching rule found"},
        ),
        tool_name=tool_name,
        tool_input=tool_input,
    )


def _rule_matches_tool_input(
    tool_name: str,
    tool_input: dict[str, Any],
    rule: PermissionRule,
    mcp_info: dict[str, Any] | None = None,
) -> bool:
    """Check if a rule matches a tool and its input."""
    # First check if the tool name matches
    if not _tool_name_matches_rule(tool_name, rule, mcp_info):
        return False

    # If rule has no content, it matches the entire tool
    if rule.rule_value.rule_content is None:
        return True

    # Check if rule content matches input
    return _rule_content_matches_input(rule.rule_value.rule_content, tool_input)


def _tool_name_matches_rule(
    tool_name: str,
    rule: PermissionRule,
    mcp_info: dict[str, Any] | None = None,
) -> bool:
    """Check if a tool name matches a rule's tool name."""
    rule_tool_name = rule.rule_value.tool_name

    # Exact match
    if rule_tool_name == tool_name:
        return True

    # MCP tool matching
    if mcp_info:
        server_name = mcp_info.get("server_name", "")
        # Match mcp__servername
        if rule_tool_name == f"mcp__{server_name}":
            return True
        # Match full mcp__servername__toolname
        full_name = f"mcp__{server_name}__{tool_name}"
        if rule_tool_name == full_name:
            return True

    return False


def _rule_content_matches_input(
    rule_content: str,
    tool_input: dict[str, Any],
) -> bool:
    """Check if rule content matches tool input."""
    import fnmatch

    # Get relevant input values to check
    input_values = []
    for key in ["command", "path", "file_path", "directory", "content"]:
        if key in tool_input:
            input_values.append(str(tool_input[key]))

    if not input_values:
        return False

    # Check if any input value matches the rule content
    for value in input_values:
        # Direct match
        if value == rule_content:
            return True

        # Glob pattern match
        if fnmatch.fnmatch(value, rule_content):
            return True

        # Prefix match (for path patterns)
        if rule_content.endswith("**"):
            prefix = rule_content[:-2]
            if value.startswith(prefix):
                return True

    return False


def format_permission_rules_for_display(rules: list[PermissionRule]) -> str:
    """Format a list of permission rules for display."""
    if not rules:
        return "No permission rules configured."

    lines = []
    for rule in rules:
        rule_str = permission_rule_value_to_string(rule.rule_value)
        lines.append(
            f"  - [{rule.rule_behavior}] {rule_str} (from {permission_rule_source_display_string(rule.source)})"
        )

    return "\n".join(lines)
