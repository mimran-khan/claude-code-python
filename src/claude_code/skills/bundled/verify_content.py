"""
Inlined reference files for the /verify bundled skill.

Migrated from: skills/bundled/verifyContent.ts (markdown assets were not in workspace).
"""

from __future__ import annotations

SKILL_MD = """---
description: Verify a code change does what it should by running the app.
---

# Verify

1. Identify what changed and the user-facing or API surface affected.
2. Run the project's automated tests (unit, integration) using the repo's standard command.
3. For UI changes, exercise the critical path manually or with browser automation if available.
4. For services, hit health and key endpoints after starting the stack as documented.
5. Summarize evidence (commands run, results, screenshots if applicable).
"""

SKILL_FILES: dict[str, str] = {
    "examples/cli.md": """# CLI verification

Run the CLI entrypoint with `--help` and a smoke command from the project README.
Capture stdout/stderr and exit code.
""",
    "examples/server.md": """# Server verification

Start the dev server using the documented command, wait for ready logs, then curl documented endpoints.
""",
}
