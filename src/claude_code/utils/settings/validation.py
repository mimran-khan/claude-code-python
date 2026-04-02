"""
Settings validation.

Functions for validating Claude Code settings.

Migrated from: utils/settings/validation.ts (350 lines) - Core logic
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ValidationError:
    """A settings validation error."""

    path: str
    message: str
    field: str | None = None
    severity: str = "error"


def validate_settings(data: dict[str, Any]) -> list[ValidationError]:
    """
    Validate a settings dictionary.

    Args:
        data: The settings dictionary to validate

    Returns:
        List of validation errors (empty if valid)
    """
    errors: list[ValidationError] = []

    # Validate permissions section
    if "permissions" in data:
        errors.extend(_validate_permissions(data["permissions"]))

    # Validate hooks section
    if "hooks" in data:
        errors.extend(_validate_hooks(data["hooks"]))

    # Validate MCP servers section
    if "mcpServers" in data:
        errors.extend(_validate_mcp_servers(data["mcpServers"]))

    # Validate env section
    if "env" in data:
        errors.extend(_validate_env(data["env"]))

    return errors


def _validate_permissions(permissions: Any) -> list[ValidationError]:
    """Validate the permissions section."""
    errors: list[ValidationError] = []

    if not isinstance(permissions, dict):
        errors.append(
            ValidationError(
                path="permissions",
                message="Permissions must be an object",
            )
        )
        return errors

    # Validate rule arrays
    for key in ["allow", "deny", "ask"]:
        if key in permissions:
            rules = permissions[key]
            if not isinstance(rules, list):
                errors.append(
                    ValidationError(
                        path=f"permissions.{key}",
                        message=f"permissions.{key} must be an array",
                    )
                )
            else:
                for i, rule in enumerate(rules):
                    if not isinstance(rule, str):
                        errors.append(
                            ValidationError(
                                path=f"permissions.{key}[{i}]",
                                message="Permission rule must be a string",
                            )
                        )

    # Validate defaultMode
    if "defaultMode" in permissions:
        valid_modes = ["default", "plan", "acceptEdits", "bypassPermissions", "dontAsk"]
        if permissions["defaultMode"] not in valid_modes:
            errors.append(
                ValidationError(
                    path="permissions.defaultMode",
                    message=f"Invalid defaultMode. Must be one of: {', '.join(valid_modes)}",
                )
            )

    # Validate additionalDirectories
    if "additionalDirectories" in permissions:
        dirs = permissions["additionalDirectories"]
        if not isinstance(dirs, list):
            errors.append(
                ValidationError(
                    path="permissions.additionalDirectories",
                    message="additionalDirectories must be an array",
                )
            )
        else:
            for i, d in enumerate(dirs):
                if not isinstance(d, str):
                    errors.append(
                        ValidationError(
                            path=f"permissions.additionalDirectories[{i}]",
                            message="Directory path must be a string",
                        )
                    )

    return errors


def _validate_hooks(hooks: Any) -> list[ValidationError]:
    """Validate the hooks section."""
    errors: list[ValidationError] = []

    if not isinstance(hooks, list):
        errors.append(
            ValidationError(
                path="hooks",
                message="Hooks must be an array",
            )
        )
        return errors

    for i, hook in enumerate(hooks):
        if not isinstance(hook, dict):
            errors.append(
                ValidationError(
                    path=f"hooks[{i}]",
                    message="Hook must be an object",
                )
            )
            continue

        # Validate matcher
        if "matcher" not in hook:
            errors.append(
                ValidationError(
                    path=f"hooks[{i}]",
                    message="Hook must have a 'matcher' field",
                )
            )
        elif not isinstance(hook["matcher"], dict):
            errors.append(
                ValidationError(
                    path=f"hooks[{i}].matcher",
                    message="Hook matcher must be an object",
                )
            )

        # Validate commands or http
        has_commands = "commands" in hook
        has_http = "http" in hook

        if not has_commands and not has_http:
            errors.append(
                ValidationError(
                    path=f"hooks[{i}]",
                    message="Hook must have either 'commands' or 'http' field",
                )
            )

        if has_commands:
            commands = hook["commands"]
            if not isinstance(commands, list):
                errors.append(
                    ValidationError(
                        path=f"hooks[{i}].commands",
                        message="commands must be an array",
                    )
                )
            else:
                for j, cmd in enumerate(commands):
                    if not isinstance(cmd, dict):
                        errors.append(
                            ValidationError(
                                path=f"hooks[{i}].commands[{j}]",
                                message="Command must be an object",
                            )
                        )
                    elif "command" not in cmd:
                        errors.append(
                            ValidationError(
                                path=f"hooks[{i}].commands[{j}]",
                                message="Command must have a 'command' field",
                            )
                        )

    return errors


def _validate_mcp_servers(servers: Any) -> list[ValidationError]:
    """Validate the MCP servers section."""
    errors: list[ValidationError] = []

    if not isinstance(servers, dict):
        errors.append(
            ValidationError(
                path="mcpServers",
                message="mcpServers must be an object",
            )
        )
        return errors

    for name, config in servers.items():
        if not isinstance(config, dict):
            errors.append(
                ValidationError(
                    path=f"mcpServers.{name}",
                    message="Server config must be an object",
                )
            )
            continue

        # Must have either command or url
        has_command = "command" in config
        has_url = "url" in config

        if not has_command and not has_url:
            errors.append(
                ValidationError(
                    path=f"mcpServers.{name}",
                    message="Server must have either 'command' or 'url' field",
                )
            )

        # Validate args if present
        if "args" in config:
            args = config["args"]
            if not isinstance(args, list):
                errors.append(
                    ValidationError(
                        path=f"mcpServers.{name}.args",
                        message="args must be an array",
                    )
                )

        # Validate env if present
        if "env" in config:
            env = config["env"]
            if not isinstance(env, dict):
                errors.append(
                    ValidationError(
                        path=f"mcpServers.{name}.env",
                        message="env must be an object",
                    )
                )

    return errors


def _validate_env(env: Any) -> list[ValidationError]:
    """Validate the env section."""
    errors: list[ValidationError] = []

    if not isinstance(env, dict):
        errors.append(
            ValidationError(
                path="env",
                message="env must be an object",
            )
        )
        return errors

    for key, value in env.items():
        if not isinstance(value, (str, int, float, bool)):
            errors.append(
                ValidationError(
                    path=f"env.{key}",
                    message="Environment variable value must be a string or primitive",
                )
            )

    return errors


def format_validation_error(error: ValidationError) -> str:
    """Format a validation error for display."""
    if error.field:
        return f"[{error.path}] {error.field}: {error.message}"
    return f"[{error.path}] {error.message}"


def format_validation_errors(errors: list[ValidationError]) -> str:
    """Format multiple validation errors for display."""
    if not errors:
        return "No errors"

    return "\n".join(format_validation_error(e) for e in errors)


def filter_invalid_permission_rules(
    rules: list[str],
    errors: list[ValidationError],
) -> list[str]:
    """
    Filter out invalid permission rules based on validation errors.

    Returns only the valid rules.
    """
    # For now, return all rules - filtering would require parsing error details
    return rules
