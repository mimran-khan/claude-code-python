"""Bundled /update-config skill. Migrated from: skills/bundled/updateConfig.ts"""

from __future__ import annotations

import json

from ..bundled_registry import register_bundled_skill
from ..types import BundledSkillDefinition

SETTINGS_EXAMPLES = """## Settings File Locations

| File | Scope | Git | Use For |
|------|-------|-----|---------|
| `~/.claude/settings.json` | Global | N/A | Personal preferences |
| `.claude/settings.json` | Project | Commit | Team hooks, permissions |
| `.claude/settings.local.json` | Project | Gitignore | Personal overrides |

Later sources override earlier ones (user → project → local).

## Permissions example
```json
{ "permissions": { "allow": ["Bash(npm:*)", "Read"], "deny": ["Bash(rm -rf:*)"] } }
```

## Hooks overview
Hooks live under `hooks` with event keys (PreToolUse, PostToolUse, Stop, SessionStart, ...).
Each entry has matchers and command/prompt/agent hook definitions.
"""

HOOKS_DOCS = """## Hooks Configuration

Structure:
```json
{
  "hooks": {
    "PostToolUse": [{
      "matcher": "Write|Edit",
      "hooks": [{ "type": "command", "command": "echo ok", "timeout": 60 }]
    }]
  }
}
```

Validate JSON after edits — invalid settings files are ignored silently.
"""

UPDATE_CONFIG_PROMPT = f"""# Update Config Skill

Modify Claude Code configuration via settings.json files.

## CRITICAL: Read Before Write
Merge with existing settings — never replace entire files unless the file is new.

## When hooks are required
Automated responses to events (format on save, log bash, etc.) require hooks in settings.json.

{SETTINGS_EXAMPLES}

{HOOKS_DOCS}

## Workflow
1. Clarify scope (user / project / local)
2. Read the target file
3. Merge carefully (especially permission arrays)
4. Edit with the Edit tool
5. Summarize changes for the user
"""


def _generate_settings_schema_stub() -> str:
    """Placeholder until Zod/Pydantic export matches TS `toJSONSchema(SettingsSchema())`."""
    return json.dumps(
        {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "properties": {
                "permissions": {"type": "object"},
                "hooks": {"type": "object"},
                "env": {"type": "object"},
                "model": {"type": "string"},
                "mcpServers": {"type": "object"},
            },
            "additionalProperties": True,
        },
        indent=2,
    )


def register_update_config_skill() -> None:
    async def get_prompt_for_command(args: str, ctx: object) -> list[dict[str, str]]:
        del ctx
        if args.startswith("[hooks-only]"):
            req = args[len("[hooks-only]") :].strip()
            body = HOOKS_DOCS + ("\n\n## Task\n\n" + req if req else "")
            return [{"type": "text", "text": body}]
        prompt = UPDATE_CONFIG_PROMPT + "\n\n## Full Settings JSON Schema (stub)\n\n```json\n"
        prompt += _generate_settings_schema_stub() + "\n```"
        if args.strip():
            prompt += f"\n\n## User Request\n\n{args}"
        return [{"type": "text", "text": prompt}]

    register_bundled_skill(
        BundledSkillDefinition(
            name="update-config",
            description=(
                "Configure Claude Code via settings.json: hooks, permissions, env vars, "
                "and troubleshooting. Use the Config tool for simple toggles like theme/model."
            ),
            allowed_tools=["Read"],
            user_invocable=True,
            get_prompt_for_command=get_prompt_for_command,
        ),
    )
