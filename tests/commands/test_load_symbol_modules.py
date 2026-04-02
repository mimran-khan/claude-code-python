"""Every CommandSpec.load_symbol must be importable as a module path."""

from __future__ import annotations

import importlib
import re
from pathlib import Path

import claude_code.commands as commands_pkg
from claude_code.commands.additional_builtin_specs import ADDITIONAL_BUILTIN_COMMAND_SPECS
from claude_code.commands.commands_manifest import built_in_command_specs, internal_only_specs

_LOAD_SYMBOL_ASSIGN_RE = re.compile(r'load_symbol\s*=\s*"(claude_code\.commands[^"]+)"')


def _commands_package_dir() -> Path:
    return Path(commands_pkg.__file__).resolve().parent


def test_all_registered_command_spec_load_symbol_paths_import() -> None:
    seen: set[str] = set()
    all_specs = (
        list(built_in_command_specs())
        + list(ADDITIONAL_BUILTIN_COMMAND_SPECS)
        + list(internal_only_specs())
    )
    for spec in all_specs:
        if not spec.load_symbol or spec.load_symbol in seen:
            continue
        seen.add(spec.load_symbol)
        importlib.import_module(spec.load_symbol)


def test_every_load_symbol_literal_under_commands_package_imports() -> None:
    """Catch stale paths in CommandSpec definitions even if a spec is not in the manifest."""
    seen: set[str] = set()
    for path in _commands_package_dir().rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        for match in _LOAD_SYMBOL_ASSIGN_RE.finditer(text):
            name = match.group(1)
            if name in seen:
                continue
            seen.add(name)
            importlib.import_module(name)
