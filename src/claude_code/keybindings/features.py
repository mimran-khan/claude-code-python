"""
Feature flags for default keybinding blocks.

TypeScript uses compile-time `feature()` from bun:bundle; Python uses env for parity.

Set ``CLAUDE_CODE_FEATURES=*`` (default) to enable all optional blocks, or a
comma-separated list like ``KAIROS,QUICK_SEARCH,VOICE_MODE``.
"""

from __future__ import annotations

import os

_ALL_SENTINEL = "*"


def feature(name: str) -> bool:
    """Return True if optional feature `name` is enabled for default bindings."""
    raw = os.environ.get("CLAUDE_CODE_FEATURES", _ALL_SENTINEL).strip()
    if raw == _ALL_SENTINEL or raw == "":
        return True
    enabled = {x.strip() for x in raw.split(",") if x.strip()}
    return name in enabled


def set_features_for_testing(names: set[str] | None) -> None:
    """Replace process env for tests (pass None to clear override)."""
    import os as _os

    if names is None:
        _os.environ.pop("CLAUDE_CODE_FEATURES", None)
    else:
        _os.environ["CLAUDE_CODE_FEATURES"] = ",".join(sorted(names))
