"""
Open or create the user keybindings file and launch an editor.

Migrated from: commands/keybindings/keybindings.ts
"""

from __future__ import annotations

import os
import shlex
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from claude_code.keybindings import (
    generate_keybindings_template,
    get_keybindings_path,
    is_keybinding_customization_enabled,
)


@dataclass
class KeybindingsCallResult:
    value: str


async def call() -> KeybindingsCallResult:
    if not is_keybinding_customization_enabled():
        return KeybindingsCallResult(
            value=("Keybinding customization is not enabled. This feature is currently in preview."),
        )

    keybindings_path = Path(get_keybindings_path())
    keybindings_path.parent.mkdir(parents=True, exist_ok=True)
    file_exists = keybindings_path.exists()
    if not file_exists:
        with keybindings_path.open("x", encoding="utf-8", newline="\n") as handle:
            handle.write(generate_keybindings_template())

    editor = os.environ.get("EDITOR") or os.environ.get("VISUAL")
    if not editor:
        action = "Opened" if file_exists else "Created"
        return KeybindingsCallResult(
            value=(f"{action} {keybindings_path}. Set EDITOR or VISUAL to open it automatically."),
        )

    editor_parts = shlex.split(editor, posix=os.name != "nt")
    if not editor_parts:
        action = "Opened" if file_exists else "Created"
        return KeybindingsCallResult(
            value=(f"{action} {keybindings_path}. EDITOR/VISUAL is empty after parsing."),
        )

    editor_exe = shutil.which(editor_parts[0])
    if editor_exe is None:
        action = "Opened" if file_exists else "Created"
        ed = editor_parts[0]
        return KeybindingsCallResult(
            value=(f"{action} {keybindings_path}. Could not resolve editor {ed!r} in PATH."),
        )

    try:
        subprocess.run(
            [editor_exe, *editor_parts[1:], str(keybindings_path)],
            check=False,
            timeout=300,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        action = "Opened" if file_exists else "Created"
        return KeybindingsCallResult(
            value=(f"{action} {keybindings_path}. Could not open in editor: {exc}"),
        )

    if file_exists:
        msg = f"Opened {keybindings_path} in your editor."
    else:
        msg = f"Created {keybindings_path} with template. Opened in your editor."
    return KeybindingsCallResult(value=msg)
