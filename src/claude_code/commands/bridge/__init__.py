"""
/remote-control — bridge remote control entry (lazy UI).

Migrated from: commands/bridge/index.ts

Imports avoid ``claude_code.bridge`` package ``__init__`` (heavy optional deps).
"""

from __future__ import annotations

import importlib.util
import os
from pathlib import Path

from claude_code.commands.spec import CommandSpec


def _load_bridge_enabled_module():
    """Load bridge_enabled.py without executing claude_code.bridge.__init__."""
    path = Path(__file__).resolve().parents[2] / "bridge" / "bridge_enabled.py"
    spec = importlib.util.spec_from_file_location(
        "_claude_code_bridge_enabled_only",
        path,
    )
    if spec is None or spec.loader is None:
        raise ImportError("bridge_enabled.py not found")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_be = _load_bridge_enabled_module()


def _bridge_feature_enabled() -> bool:
    return os.environ.get("CLAUDE_CODE_BRIDGE_MODE", "1") == "1"


def _is_enabled() -> bool:
    return _bridge_feature_enabled() and _be.is_bridge_enabled()


def _is_hidden() -> bool:
    return not _is_enabled()


REMOTE_CONTROL_COMMAND = CommandSpec(
    type="local-jsx",
    name="remote-control",
    aliases=("rc",),
    description="Connect this terminal for remote-control sessions",
    argument_hint="[name]",
    immediate=True,
    is_enabled=_is_enabled,
    is_hidden_fn=_is_hidden,
    load_symbol="claude_code.commands.bridge.ui",
)

__all__ = ["REMOTE_CONTROL_COMMAND"]
