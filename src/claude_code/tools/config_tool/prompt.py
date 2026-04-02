"""Dynamic prompt generation for the Config tool.

Migrated from: tools/ConfigTool/prompt.ts (simplified)
"""

from __future__ import annotations

from .constants import DESCRIPTION
from .supported_settings import SUPPORTED_SETTINGS, get_options_for_setting


def generate_prompt() -> str:
    global_lines: list[str] = []
    project_lines: list[str] = []
    for key, cfg in sorted(SUPPORTED_SETTINGS.items()):
        if key == "model":
            continue
        opts = get_options_for_setting(key)
        if opts:
            line = f"- {key}: {', '.join(repr(o) for o in opts)} - {cfg.description}"
        elif cfg.type == "boolean":
            line = f"- {key}: true/false - {cfg.description}"
        else:
            line = f"- {key} - {cfg.description}"
        if cfg.source == "global":
            global_lines.append(line)
        else:
            project_lines.append(line)

    return f"""{DESCRIPTION}

View or change Claude Code settings. Use when the user requests configuration changes, asks about current settings, or when adjusting a setting would benefit them.

## Usage
- **Get current value:** Omit the "value" parameter
- **Set new value:** Include the "value" parameter

## Configurable settings list

### Global Settings (stored in ~/.claude.json)
{chr(10).join(global_lines)}

### Project Settings (stored in settings.json)
{chr(10).join(project_lines)}

### Model
- model: string — override the default model (options depend on deployment)

## Examples
- Get theme: {{"setting": "theme"}}
- Set dark theme: {{"setting": "theme", "value": "dark"}}
- Change permission mode: {{"setting": "permissions.defaultMode", "value": "plan"}}
"""
