"""
Permission Checker.

Handles checking permissions for tool execution.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from .types import (
    PermissionBehavior,
    PermissionContext,
    PermissionDecision,
    PermissionDecisionReason,
    PermissionRule,
    PermissionRuleSource,
    permission_rule_value_from_string,
)

if TYPE_CHECKING:
    pass


# Rule source priority (lower index = higher priority)
RULE_SOURCE_PRIORITY: list[PermissionRuleSource] = [
    "enterprise",
    "enterpriseGlobal",
    "enterpriseProjectPublic",
    "cliArg",
    "command",
    "session",
    "project",
    "projectPublic",
    "global",
]


@dataclass
class PermissionChecker:
    """Permission checker for tool execution."""

    context: PermissionContext = field(default_factory=PermissionContext)

    def check(
        self,
        tool_name: str,
        input_value: str | None = None,
    ) -> PermissionDecision:
        """Check permission for a tool.

        Args:
            tool_name: The name of the tool
            input_value: Optional input value for pattern matching

        Returns:
            PermissionDecision indicating allow, deny, or ask
        """
        # Check mode-based bypass
        if self.context.mode == "bypassPermissions":
            return PermissionDecision(
                decision="allow",
                reason=PermissionDecisionReason(
                    type="mode",
                    message="Bypass permissions mode enabled",
                ),
            )

        # Check sandbox mode
        if self.context.sandbox_enabled:
            return PermissionDecision(
                decision="allow",
                reason=PermissionDecisionReason(
                    type="sandbox",
                    message="Running in sandbox mode",
                ),
            )

        # Get applicable rules
        rules = self.get_rules(tool_name, input_value)

        # Check deny rules first (they take priority over allow)
        for rule in rules:
            if rule.behavior == "deny" and rule.matches(tool_name, input_value):
                return PermissionDecision(
                    decision="deny",
                    reason=PermissionDecisionReason(
                        type="rule",
                        rule=rule,
                        message=f"Denied by {rule.source} rule",
                    ),
                )

        # Check allow rules
        for rule in rules:
            if rule.behavior == "allow" and rule.matches(tool_name, input_value):
                return PermissionDecision(
                    decision="allow",
                    reason=PermissionDecisionReason(
                        type="rule",
                        rule=rule,
                        message=f"Allowed by {rule.source} rule",
                    ),
                )

        # Default: ask
        return PermissionDecision(
            decision="ask",
            reason=PermissionDecisionReason(
                type="default",
                message="No matching rule found",
            ),
        )

    def get_rules(
        self,
        tool_name: str,
        input_value: str | None = None,
    ) -> list[PermissionRule]:
        """Get all applicable rules for a tool, sorted by priority."""
        rules: list[PermissionRule] = []

        # Collect rules from all sources in priority order
        for source in RULE_SOURCE_PRIORITY:
            # Get allow rules
            allow_strings = self._get_rules_for_source(source, "allow")
            for rule_string in allow_strings:
                rule_value = permission_rule_value_from_string(rule_string)
                if rule_value.matches(tool_name, input_value):
                    rules.append(
                        PermissionRule(
                            source=source,
                            behavior="allow",
                            value=rule_value,
                        )
                    )

            # Get deny rules
            deny_strings = self._get_rules_for_source(source, "deny")
            for rule_string in deny_strings:
                rule_value = permission_rule_value_from_string(rule_string)
                if rule_value.matches(tool_name, input_value):
                    rules.append(
                        PermissionRule(
                            source=source,
                            behavior="deny",
                            value=rule_value,
                        )
                    )

        return rules

    def _get_rules_for_source(
        self,
        source: PermissionRuleSource,
        behavior: PermissionBehavior,
    ) -> list[str]:
        """Get rules for a specific source and behavior."""
        if source == "session":
            if behavior == "allow":
                return self.context.session_allow_rules
            return self.context.session_deny_rules

        if behavior == "allow":
            return self.context.always_allow_rules.get(source, [])
        return self.context.always_deny_rules.get(source, [])

    def add_rule(
        self,
        rule_string: str,
        behavior: PermissionBehavior,
        source: PermissionRuleSource = "session",
    ) -> None:
        """Add a permission rule."""
        if source == "session":
            if behavior == "allow":
                self.context.add_session_allow_rule(rule_string)
            else:
                self.context.add_session_deny_rule(rule_string)
        else:
            if behavior == "allow":
                if source not in self.context.always_allow_rules:
                    self.context.always_allow_rules[source] = []
                if rule_string not in self.context.always_allow_rules[source]:
                    self.context.always_allow_rules[source].append(rule_string)
            else:
                if source not in self.context.always_deny_rules:
                    self.context.always_deny_rules[source] = []
                if rule_string not in self.context.always_deny_rules[source]:
                    self.context.always_deny_rules[source].append(rule_string)

    def remove_rule(
        self,
        rule_string: str,
        behavior: PermissionBehavior,
        source: PermissionRuleSource = "session",
    ) -> bool:
        """Remove a permission rule. Returns True if rule was removed."""
        if source == "session":
            if behavior == "allow":
                if rule_string in self.context.session_allow_rules:
                    self.context.session_allow_rules.remove(rule_string)
                    return True
            else:
                if rule_string in self.context.session_deny_rules:
                    self.context.session_deny_rules.remove(rule_string)
                    return True
        else:
            if behavior == "allow":
                rules = self.context.always_allow_rules.get(source, [])
                if rule_string in rules:
                    rules.remove(rule_string)
                    return True
            else:
                rules = self.context.always_deny_rules.get(source, [])
                if rule_string in rules:
                    rules.remove(rule_string)
                    return True

        return False


# Global default checker
_default_checker: PermissionChecker | None = None


def get_default_checker() -> PermissionChecker:
    """Get the default permission checker."""
    global _default_checker
    if _default_checker is None:
        _default_checker = PermissionChecker()
    return _default_checker


def set_default_checker(checker: PermissionChecker) -> None:
    """Set the default permission checker."""
    global _default_checker
    _default_checker = checker


def check_permission(
    tool_name: str,
    input_value: str | None = None,
    *,
    checker: PermissionChecker | None = None,
) -> PermissionDecision:
    """Check permission for a tool using the default or provided checker."""
    if checker is None:
        checker = get_default_checker()
    return checker.check(tool_name, input_value)


def get_permission_rules(
    tool_name: str,
    input_value: str | None = None,
    *,
    checker: PermissionChecker | None = None,
) -> list[PermissionRule]:
    """Get all applicable rules for a tool."""
    if checker is None:
        checker = get_default_checker()
    return checker.get_rules(tool_name, input_value)
