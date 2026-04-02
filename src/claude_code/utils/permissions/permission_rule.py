"""
Permission rule types and utilities.

Defines permission rules, behaviors, and sources.

Migrated from: utils/permissions/PermissionRule.ts (41 lines)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

# Permission behavior type
PermissionBehavior = Literal["allow", "deny", "ask"]

# Permission rule source type
PermissionRuleSource = Literal[
    "userSettings",
    "projectSettings",
    "localSettings",
    "flagSettings",
    "policySettings",
    "cliArg",
    "command",
    "session",
]


@dataclass
class PermissionRuleValue:
    """
    The value of a permission rule.

    Attributes:
        tool_name: The name of the tool this rule applies to
        rule_content: Optional content of the rule. Each tool may
                     implement custom handling in checkPermissions()
    """

    tool_name: str
    rule_content: str | None = None


@dataclass
class PermissionRule:
    """
    A permission rule with its source and behavior.

    Attributes:
        source: Where the rule originated from
        rule_behavior: Whether to allow, deny, or ask
        rule_value: The rule content
    """

    source: PermissionRuleSource
    rule_behavior: PermissionBehavior
    rule_value: PermissionRuleValue


def get_rule_behavior_description(behavior: PermissionBehavior) -> str:
    """Get a prose description for a rule behavior."""
    if behavior == "allow":
        return "allowed"
    elif behavior == "deny":
        return "denied"
    else:
        return "asked for confirmation for"


def create_permission_rule(
    source: PermissionRuleSource,
    behavior: PermissionBehavior,
    tool_name: str,
    rule_content: str | None = None,
) -> PermissionRule:
    """Create a new permission rule."""
    return PermissionRule(
        source=source,
        rule_behavior=behavior,
        rule_value=PermissionRuleValue(
            tool_name=tool_name,
            rule_content=rule_content,
        ),
    )


def rule_matches_tool(rule: PermissionRule, tool_name: str) -> bool:
    """Check if a rule applies to a specific tool."""
    return rule.rule_value.tool_name == tool_name


def rule_has_content(rule: PermissionRule) -> bool:
    """Check if a rule has content."""
    return rule.rule_value.rule_content is not None
