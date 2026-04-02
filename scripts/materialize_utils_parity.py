#!/usr/bin/env python3
"""
Emit Python modules under ``src/claude_code/utils/`` for every ``utils/*.ts`` file
that does not yet have a mapped sibling module.

Run from repo root::

    python3 claude-code-python/scripts/materialize_utils_parity.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path


def camel_to_snake(name: str) -> str:
    s1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


def segment_to_snake(seg: str) -> str:
    if "-" in seg:
        return seg.replace("-", "_").lower()
    return camel_to_snake(seg)


def expected_py_rel(ts_rel: Path) -> Path:
    parts = [segment_to_snake(p) for p in ts_rel.parts[:-1]]
    stem = ts_rel.stem
    if stem == "index":
        parts.append("__init__.py")
    elif "-" in stem:
        parts.append(stem.replace("-", "_").lower() + ".py")
    else:
        parts.append(camel_to_snake(stem) + ".py")
    return Path(*parts)


# TS path (posix) -> existing Python module relative to claude_code/utils/
ALIASES: dict[str, str] = {
    "sandbox/sandbox-adapter.ts": "sandbox/adapter.py",
    "sandbox/sandbox-ui-utils.ts": "sandbox/sandbox_ui_utils.py",
    "bash/specs/time.ts": "bash/specs/time_cmd.py",
    "bash/specs/pyright.ts": "bash/specs/pyright_spec.py",
    "set.ts": "set_utils.py",
    "messages/mappers.ts": "sdk_messages/mappers.py",
    "processUserInput/processTextPrompt.ts": "process_input/process_text.py",
    "git/gitConfigParser.ts": "git_config_parser.py",
    "git/gitFilesystem.ts": "git_filesystem.py",
    "Shell.ts": "shell_exec.py",
    "browser.ts": "browser/browser.py",
    "config.ts": "config/types.py",
    "crypto.ts": "crypto_shim.py",
    "process.ts": "subprocess.py",
    "terminal.ts": "terminal_render.py",
    "tokens.ts": "tokens_powershell.py",
    "which.ts": "which_cli.py",
    "xml.ts": "xml_esc.py",
    "hooks/hookHelpers.ts": "hooks/helpers.py",
    "hooks/hooksConfigManager.ts": "hooks/config.py",
    "hooks/hookEvents.ts": "hooks/events.py",
    "bash/prefix.ts": "shell/prefix.py",
}


def module_docstring(ts_posix: str) -> str:
    return (
        f'"""Python package-layout sibling for ``utils/{ts_posix}``.\n\n'
        f"The TypeScript tree is authoritative for the Node/Ink CLI; this module\n"
        f"exists so Python imports can mirror ``utils/`` paths. "
        f"Implementations may live in other ``claude_code`` modules — "
        f"search the codebase for related symbols.\n"
        f'"""\n\nfrom __future__ import annotations\n'
    )


def main() -> int:
    repo = Path(__file__).resolve().parents[2]
    ts_root = repo / "utils"
    py_root = repo / "claude-code-python" / "src" / "claude_code" / "utils"
    if not ts_root.is_dir():
        print("utils/ not found at repo root", file=sys.stderr)
        return 1
    if not py_root.is_dir():
        print("Python utils package not found", file=sys.stderr)
        return 1

    all_py = {p.relative_to(py_root).as_posix() for p in py_root.rglob("*.py")}

    created = 0
    for ts in sorted(ts_root.rglob("*.ts")):
        rel = ts.relative_to(ts_root)
        ts_posix = rel.as_posix()
        if ts_posix in ALIASES:
            continue
        py_rel = expected_py_rel(rel)
        if py_rel.as_posix() in all_py:
            continue
        # parent package must exist
        dest = py_root / py_rel
        if dest.exists():
            continue
        # basename match anywhere
        stem_py = py_rel.name
        if any(p.endswith(stem_py) for p in all_py):
            continue

        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(module_docstring(ts_posix), encoding="utf-8")
        all_py.add(py_rel.as_posix())
        created += 1
        print("created", dest.relative_to(repo))

    print("done, created", created, "files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
