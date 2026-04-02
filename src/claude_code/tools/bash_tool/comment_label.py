"""
Extract a human-facing label from a leading ``#`` comment on the first line.

Migrated from: tools/BashTool/commentLabel.ts
"""


def extract_bash_comment_label(command: str) -> str | None:
    nl = command.find("\n")
    first = (command if nl == -1 else command[:nl]).strip()
    if not first.startswith("#") or first.startswith("#!"):
        return None
    stripped = first.lstrip("#").strip()
    return stripped or None


__all__ = ["extract_bash_comment_label"]
