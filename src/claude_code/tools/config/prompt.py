"""
Config Tool Prompt.

Contains the tool name, description, and prompt generation.
"""

from __future__ import annotations

CONFIG_TOOL_NAME = "Config"

DESCRIPTION = "Get or set Claude Code configuration settings."


# Supported settings
SUPPORTED_SETTINGS = {
    "theme": {
        "type": "string",
        "options": ["dark", "light", "system"],
        "description": "Color theme for the UI",
        "source": "global",
    },
    "verbose": {
        "type": "boolean",
        "description": "Enable verbose output",
        "source": "global",
    },
    "editorMode": {
        "type": "string",
        "options": ["normal", "vim"],
        "description": "Editor keybinding mode",
        "source": "global",
    },
    "model": {
        "type": "string",
        "description": "Override the default model",
        "source": "project",
    },
    "permissions.defaultMode": {
        "type": "string",
        "options": ["default", "plan", "auto"],
        "description": "Default permission mode",
        "source": "project",
    },
}


def generate_prompt() -> str:
    """Generate the prompt documentation from the registry."""
    global_settings: list[str] = []
    project_settings: list[str] = []

    for key, config in SUPPORTED_SETTINGS.items():
        if key == "model":
            continue

        options = config.get("options")
        line = f"- {key}"

        if options:
            quoted_opts = ", ".join(f'"{o}"' for o in options)
            line += f": {quoted_opts}"
        elif config["type"] == "boolean":
            line += ": true/false"

        line += f" - {config['description']}"

        if config["source"] == "global":
            global_settings.append(line)
        else:
            project_settings.append(line)

    model_section = """## Model
- model - Override the default model (sonnet, opus, haiku, best, or full model ID)"""

    return f"""Get or set Claude Code configuration settings.

View or change Claude Code settings. Use when the user requests configuration changes, asks about current settings, or when adjusting a setting would benefit them.

## Usage
- **Get current value:** Omit the "value" parameter
- **Set new value:** Include the "value" parameter

## Configurable settings list
The following settings are available for you to change:

### Global Settings (stored in ~/.claude.json)
{chr(10).join(global_settings)}

### Project Settings (stored in settings.json)
{chr(10).join(project_settings)}

{model_section}

## Examples
- Get theme: {{ "setting": "theme" }}
- Set dark theme: {{ "setting": "theme", "value": "dark" }}
- Enable vim mode: {{ "setting": "editorMode", "value": "vim" }}
- Enable verbose: {{ "setting": "verbose", "value": true }}
- Change model: {{ "setting": "model", "value": "opus" }}
- Change permission mode: {{ "setting": "permissions.defaultMode", "value": "plan" }}
"""
