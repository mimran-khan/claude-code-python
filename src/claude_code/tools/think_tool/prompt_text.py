"""Think tool — private reasoning scratchpad (no TS in leak)."""

from __future__ import annotations

THINK_TOOL_NAME = "Think"

DESCRIPTION = (
    "Record structured reasoning for the current turn. Does not change workspace state; "
    "use for planning before other tools."
)

PROMPT = """
Summarize your reasoning, assumptions, and plan. This content is for transparency and
self-correction; keep it concise and avoid duplicating information you will put in the user reply.
""".strip()
