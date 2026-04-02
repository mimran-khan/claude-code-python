"""
Vim / normal readline mode toggle.

Migrated from: commands/vim/vim.ts
"""

from __future__ import annotations

from typing import Any

from claude_code.utils.config_utils import get_global_config, save_global_config


async def call() -> dict[str, str]:
    cfg = get_global_config()
    current = cfg.editor_mode or "normal"
    if current == "emacs":
        current = "normal"
    if current == "default":
        current = "normal"
    new_mode = "vim" if current == "normal" else "normal"

    def _upd(prev: dict[str, Any]) -> dict[str, Any]:
        out = {**prev, "editorMode": new_mode}
        return out

    save_global_config(_upd)

    if new_mode == "vim":
        msg = "Editor mode set to vim. Use Escape key to toggle between INSERT and NORMAL modes."
    else:
        msg = "Editor mode set to normal. Using standard (readline) keyboard bindings."
    return {"type": "text", "value": msg}


__all__ = ["call"]
