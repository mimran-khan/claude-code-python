"""
Permission rule parsing utilities.

Functions for parsing and serializing permission rule strings.

Migrated from: utils/permissions/permissionRuleParser.ts (199 lines)
"""

from __future__ import annotations

from .permission_rule import PermissionRuleValue

# Legacy tool name aliases
LEGACY_TOOL_NAME_ALIASES: dict[str, str] = {
    "Task": "Agent",
    "KillShell": "TaskStop",
    "AgentOutputTool": "TaskOutput",
    "BashOutputTool": "TaskOutput",
}


def normalize_legacy_tool_name(name: str) -> str:
    """Normalize a legacy tool name to its canonical name."""
    return LEGACY_TOOL_NAME_ALIASES.get(name, name)


def get_legacy_tool_names(canonical_name: str) -> list[str]:
    """Get all legacy names for a canonical tool name."""
    result = []
    for legacy, canonical in LEGACY_TOOL_NAME_ALIASES.items():
        if canonical == canonical_name:
            result.append(legacy)
    return result


def escape_rule_content(content: str) -> str:
    r"""
    Escape special characters in rule content for safe storage.

    Permission rules use the format "Tool(content)", so parentheses
    in content must be escaped.

    Escaping order matters:
    1. Escape existing backslashes first (\ -> \\)
    2. Then escape parentheses (( -> \(, ) -> \))

    Examples:
        escape_rule_content('psycopg2.connect()') => 'psycopg2.connect\(\)'
        escape_rule_content('echo "test\nvalue"') => 'echo "test\\nvalue"'
    """
    return (
        content.replace("\\", "\\\\")  # Escape backslashes first
        .replace("(", "\\(")  # Escape opening parentheses
        .replace(")", "\\)")  # Escape closing parentheses
    )


def unescape_rule_content(content: str) -> str:
    r"""
    Unescape special characters in rule content after parsing.

    Unescaping order matters (reverse of escaping):
    1. Unescape parentheses first (\( -> (, \) -> ))
    2. Then unescape backslashes (\\ -> \)

    Examples:
        unescape_rule_content('psycopg2.connect\(\)') => 'psycopg2.connect()'
        unescape_rule_content('echo "test\\nvalue"') => 'echo "test\nvalue"'
    """
    return (
        content.replace("\\(", "(")  # Unescape opening parentheses
        .replace("\\)", ")")  # Unescape closing parentheses
        .replace("\\\\", "\\")  # Unescape backslashes last
    )


def _find_first_unescaped_char(s: str, char: str) -> int:
    """Find the first unescaped occurrence of a character."""
    i = 0
    while i < len(s):
        if s[i] == "\\" and i + 1 < len(s):
            # Skip escaped character
            i += 2
            continue
        if s[i] == char:
            return i
        i += 1
    return -1


def _find_last_unescaped_char(s: str, char: str) -> int:
    """Find the last unescaped occurrence of a character."""
    i = len(s) - 1
    while i >= 0:
        # Check if this position is escaped
        backslash_count = 0
        j = i - 1
        while j >= 0 and s[j] == "\\":
            backslash_count += 1
            j -= 1

        # If odd number of backslashes, this char is escaped
        if s[i] == char and backslash_count % 2 == 0:
            return i
        i -= 1
    return -1


def permission_rule_value_from_string(rule_string: str) -> PermissionRuleValue:
    r"""
    Parse a permission rule string into its components.

    Handles escaped parentheses in the content portion.

    Format: "ToolName" or "ToolName(content)"
    Content may contain escaped parentheses: \( and \)

    Examples:
        permission_rule_value_from_string('Bash')
            => PermissionRuleValue(tool_name='Bash')
        permission_rule_value_from_string('Bash(npm install)')
            => PermissionRuleValue(tool_name='Bash', rule_content='npm install')
        permission_rule_value_from_string('Bash(python -c "print\(1\)")')
            => PermissionRuleValue(tool_name='Bash', rule_content='python -c "print(1)"')
    """
    # Find the first unescaped opening parenthesis
    open_paren_index = _find_first_unescaped_char(rule_string, "(")
    if open_paren_index == -1:
        # No parenthesis found - this is just a tool name
        return PermissionRuleValue(tool_name=normalize_legacy_tool_name(rule_string))

    # Find the last unescaped closing parenthesis
    close_paren_index = _find_last_unescaped_char(rule_string, ")")
    if close_paren_index == -1 or close_paren_index <= open_paren_index:
        # No matching closing paren or malformed - treat as tool name
        return PermissionRuleValue(tool_name=normalize_legacy_tool_name(rule_string))

    # Ensure the closing paren is at the end
    if close_paren_index != len(rule_string) - 1:
        # Content after closing paren - treat as tool name
        return PermissionRuleValue(tool_name=normalize_legacy_tool_name(rule_string))

    tool_name = rule_string[:open_paren_index]
    raw_content = rule_string[open_paren_index + 1 : close_paren_index]

    # Missing toolName (e.g., "(foo)") is malformed - treat whole string as tool name
    if not tool_name:
        return PermissionRuleValue(tool_name=normalize_legacy_tool_name(rule_string))

    # Empty content (e.g., "Bash()") or standalone wildcard (e.g., "Bash(*)")
    # should be treated as just the tool name (tool-wide rule)
    if raw_content == "" or raw_content == "*":
        return PermissionRuleValue(tool_name=normalize_legacy_tool_name(tool_name))

    # Unescape the content
    rule_content = unescape_rule_content(raw_content)
    return PermissionRuleValue(
        tool_name=normalize_legacy_tool_name(tool_name),
        rule_content=rule_content,
    )


def permission_rule_value_to_string(rule_value: PermissionRuleValue) -> str:
    r"""
    Convert a permission rule value to its string representation.

    Escapes parentheses in the content to prevent parsing issues.

    Examples:
        permission_rule_value_to_string(PermissionRuleValue(tool_name='Bash'))
            => 'Bash'
        permission_rule_value_to_string(PermissionRuleValue(tool_name='Bash', rule_content='npm install'))
            => 'Bash(npm install)'
        permission_rule_value_to_string(PermissionRuleValue(tool_name='Bash', rule_content='python -c "print(1)"'))
            => 'Bash(python -c "print\(1\)")'
    """
    if not rule_value.rule_content:
        return rule_value.tool_name

    escaped_content = escape_rule_content(rule_value.rule_content)
    return f"{rule_value.tool_name}({escaped_content})"


def create_tool_rule_string(tool_name: str, content: str | None = None) -> str:
    """Create a rule string for a tool with optional content."""
    rule_value = PermissionRuleValue(tool_name=tool_name, rule_content=content)
    return permission_rule_value_to_string(rule_value)
