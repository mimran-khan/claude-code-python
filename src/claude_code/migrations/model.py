"""
Model name map and generic config model migration.

Per-file migrations live in sibling modules (``migrate_*_to_*.py``).
"""

from __future__ import annotations

from typing import Any

from claude_code.utils.config_utils import get_global_config, save_global_config
from claude_code.utils.debug import log_for_debugging

# Model name migrations: old -> new (baseline map; runtime migrations may further adjust)
MODEL_MIGRATIONS: dict[str, str] = {
    "claude-3-5-sonnet-20241022": "claude-sonnet-4-20250514",
    "claude-3-5-sonnet-latest": "claude-sonnet-4-20250514",
    "claude-3-5-sonnet-1m": "claude-sonnet-4-20250514",
    "claude-3-opus-20240229": "claude-opus-4-20250514",
    "claude-3-opus-latest": "claude-opus-4-20250514",
    "claude-3-opus-1m": "claude-opus-4-20250514",
    "fennec-preview": "claude-opus-4-20250514",
    "claude-2.1": "claude-sonnet-4-20250514",
    "claude-2.0": "claude-sonnet-4-20250514",
}


def migrate_model_name(model_name: str) -> str:
    """Return the canonical replacement model id for a legacy name, or the input."""
    return MODEL_MIGRATIONS.get(model_name, model_name)


def migrate_model_in_config() -> bool:
    """Rewrite ``model`` in global config when it matches ``MODEL_MIGRATIONS``."""
    try:
        config = get_global_config()
        current_model = config.model
        if not current_model:
            return True
        new_model = migrate_model_name(current_model)
        if new_model == current_model:
            return True

        def updater(current: dict[str, Any]) -> dict[str, Any]:
            current = dict(current)
            current["model"] = new_model
            return current

        save_global_config(updater)
        log_for_debugging(f"migration: model {current_model} -> {new_model}")
        return True
    except Exception as exc:
        log_for_debugging(f"migration: model migration failed: {exc}")
        return False
