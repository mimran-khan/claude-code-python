"""
/btw — quick side question without interrupting main thread.

Migrated from: commands/btw/index.ts
"""

from __future__ import annotations

from claude_code.commands.spec import CommandSpec

BTW_COMMAND = CommandSpec(
    type="local-jsx",
    name="btw",
    description="Ask a quick side question without interrupting the main conversation",
    immediate=True,
    argument_hint="<question>",
    load_symbol="claude_code.commands.btw.ui",
)

__all__ = ["BTW_COMMAND"]
