"""
Permission Types.

Type definitions for the permission system.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    pass

# Permission behaviors
PermissionBehavior = Literal["allow", "deny", "ask"]

# Permission modes
PermissionMode = Literal[
    "default",
    "acceptEdits",
    "bypassPermissions",
    "plan",
]

# Permission rule sources
PermissionRuleSource = Literal[
    "enterprise",
    "enterpriseGlobal",
    "enterpriseProjectPublic",
    "global",
    "project",
    "projectPublic",
    "cliArg",
    "command",
    "session",
]

# Decision types
PermissionDecisionType = Literal[
    "allow",
    "deny",
    "ask",
]


@dataclass
class PermissionRuleValue:
    """Parsed permission rule value."""

    tool_name: str
    pattern: str | None = None
    is_glob: bool = False

    def matches(self, tool_name: str, input_value: str | None = None) -> bool:
        """Check if rule matches the given tool and input."""
        if self.tool_name != tool_name:
            return False

        if self.pattern is None:
            return True

        if input_value is None:
            return False

        if self.is_glob:
            import fnmatch

            return fnmatch.fnmatch(input_value, self.pattern)

        return input_value == self.pattern


@dataclass
class PermissionRule:
    """A permission rule."""

    source: PermissionRuleSource
    behavior: PermissionBehavior
    value: PermissionRuleValue

    def matches(self, tool_name: str, input_value: str | None = None) -> bool:
        """Check if rule matches the given tool and input."""
        return self.value.matches(tool_name, input_value)


@dataclass
class PermissionDecisionReason:
    """Reason for a permission decision."""

    type: Literal["rule", "hook", "classifier", "mode", "sandbox", "default"]
    rule: PermissionRule | None = None
    message: str = ""
    classifier: str | None = None
    reason: str = ""


@dataclass
class PermissionDecision:
    """Result of a permission check."""

    decision: PermissionDecisionType
    reason: PermissionDecisionReason | None = None

    @property
    def is_allowed(self) -> bool:
        """Check if permission is allowed."""
        return self.decision == "allow"

    @property
    def is_denied(self) -> bool:
        """Check if permission is denied."""
        return self.decision == "deny"

    @property
    def needs_ask(self) -> bool:
        """Check if permission needs user confirmation."""
        return self.decision == "ask"


@dataclass
class PermissionAskResult:
    """Result from asking user for permission."""

    granted: bool
    remember: Literal["session", "project", "global", "none"] = "none"
    pattern: str | None = None


@dataclass
class PermissionResult:
    """Complete permission result."""

    decision: PermissionDecision
    ask_result: PermissionAskResult | None = None

    @property
    def is_allowed(self) -> bool:
        """Check if permission was granted."""
        if self.decision.is_allowed:
            return True
        if self.decision.needs_ask and self.ask_result:
            return self.ask_result.granted
        return False


@dataclass
class PermissionContext:
    """Context for permission checking."""

    mode: PermissionMode = "default"

    # Rule storage by source
    always_allow_rules: dict[PermissionRuleSource, list[str]] = field(default_factory=dict)
    always_deny_rules: dict[PermissionRuleSource, list[str]] = field(default_factory=dict)

    # Session rules (temporary)
    session_allow_rules: list[str] = field(default_factory=list)
    session_deny_rules: list[str] = field(default_factory=list)

    # MCP permissions
    mcp_allowed_servers: set[str] = field(default_factory=set)
    mcp_denied_servers: set[str] = field(default_factory=set)

    # Sandbox mode
    sandbox_enabled: bool = False

    def add_session_allow_rule(self, rule: str) -> None:
        """Add a session-level allow rule."""
        if rule not in self.session_allow_rules:
            self.session_allow_rules.append(rule)

    def add_session_deny_rule(self, rule: str) -> None:
        """Add a session-level deny rule."""
        if rule not in self.session_deny_rules:
            self.session_deny_rules.append(rule)

    def clear_session_rules(self) -> None:
        """Clear all session-level rules."""
        self.session_allow_rules.clear()
        self.session_deny_rules.clear()


def permission_rule_value_from_string(rule_string: str) -> PermissionRuleValue:
    """Parse a permission rule string into a PermissionRuleValue."""
    parts = rule_string.split(":", 1)
    tool_name = parts[0]

    if len(parts) == 1:
        return PermissionRuleValue(tool_name=tool_name)

    pattern = parts[1]
    is_glob = "*" in pattern or "?" in pattern

    return PermissionRuleValue(
        tool_name=tool_name,
        pattern=pattern,
        is_glob=is_glob,
    )


def permission_rule_value_to_string(value: PermissionRuleValue) -> str:
    """Convert a PermissionRuleValue to a rule string."""
    if value.pattern is None:
        return value.tool_name
    return f"{value.tool_name}:{value.pattern}"
