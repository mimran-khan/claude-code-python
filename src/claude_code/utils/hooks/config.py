"""
Hook configuration management.

Loading and managing hook configs.

Migrated from: utils/hooks/hooksConfigManager.ts + hooksSettings.ts
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

HookEvent = Literal[
    "PreToolUse",
    "PostToolUse",
    "Stop",
    "Notification",
    "SessionStart",
    "Setup",
]


@dataclass
class HookMatcher:
    """Matcher for hook execution."""

    tool_name: str | None = None
    tool_name_pattern: str | None = None

    def matches(self, tool_name: str) -> bool:
        """Check if the matcher matches a tool name."""
        if self.tool_name:
            return tool_name == self.tool_name

        if self.tool_name_pattern:
            return bool(re.match(self.tool_name_pattern, tool_name))

        return True


@dataclass
class HookConfig:
    """Configuration for a hook."""

    name: str
    event: HookEvent
    command: str
    matcher: HookMatcher = field(default_factory=HookMatcher)
    timeout: int = 30000
    enabled: bool = True
    description: str = ""

    @staticmethod
    def from_dict(data: dict[str, Any]) -> HookConfig:
        """Create from dictionary."""
        matcher = HookMatcher()
        if "matcher" in data:
            m = data["matcher"]
            matcher = HookMatcher(
                tool_name=m.get("toolName"),
                tool_name_pattern=m.get("toolNamePattern"),
            )

        return HookConfig(
            name=data.get("name", ""),
            event=data.get("event", "PreToolUse"),
            command=data.get("command", ""),
            matcher=matcher,
            timeout=data.get("timeout", 30000),
            enabled=data.get("enabled", True),
            description=data.get("description", ""),
        )


@dataclass
class HooksConfiguration:
    """Full hooks configuration."""

    hooks: list[HookConfig] = field(default_factory=list)
    version: str = "1.0"

    @staticmethod
    def from_dict(data: dict[str, Any]) -> HooksConfiguration:
        """Create from dictionary."""
        hooks = []
        for hook_data in data.get("hooks", []):
            hooks.append(HookConfig.from_dict(hook_data))

        return HooksConfiguration(
            hooks=hooks,
            version=data.get("version", "1.0"),
        )


def load_hooks_config(config_path: str | None = None) -> HooksConfiguration:
    """
    Load hooks configuration from file.

    Args:
        config_path: Path to config file (defaults to .claude/hooks.json)

    Returns:
        HooksConfiguration
    """
    if config_path is None:
        # Check project-level first, then user-level
        project_config = Path(".claude/hooks.json")
        if project_config.exists():
            config_path = str(project_config)
        else:
            home = os.path.expanduser("~")
            user_config = Path(home) / ".config" / "claude-code" / "hooks.json"
            if user_config.exists():
                config_path = str(user_config)

    if config_path and os.path.exists(config_path):
        try:
            with open(config_path) as f:
                data = json.load(f)
            return HooksConfiguration.from_dict(data)
        except (OSError, json.JSONDecodeError):
            pass

    return HooksConfiguration()


def get_hooks_for_event(
    config: HooksConfiguration,
    event: HookEvent,
    tool_name: str | None = None,
) -> list[HookConfig]:
    """
    Get hooks matching an event and optional tool name.

    Args:
        config: Hooks configuration
        event: Event type
        tool_name: Optional tool name to match

    Returns:
        List of matching hooks
    """
    matching = []

    for hook in config.hooks:
        if not hook.enabled:
            continue

        if hook.event != event:
            continue

        if tool_name and not hook.matcher.matches(tool_name):
            continue

        matching.append(hook)

    return matching


def save_hooks_config(
    config: HooksConfiguration,
    config_path: str,
) -> bool:
    """
    Save hooks configuration to file.

    Args:
        config: Configuration to save
        config_path: Path to save to

    Returns:
        True if saved successfully
    """
    try:
        data = {
            "version": config.version,
            "hooks": [
                {
                    "name": h.name,
                    "event": h.event,
                    "command": h.command,
                    "timeout": h.timeout,
                    "enabled": h.enabled,
                    "description": h.description,
                    "matcher": {
                        "toolName": h.matcher.tool_name,
                        "toolNamePattern": h.matcher.tool_name_pattern,
                    },
                }
                for h in config.hooks
            ],
        }

        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        with open(config_path, "w") as f:
            json.dump(data, f, indent=2)

        return True
    except OSError:
        return False
