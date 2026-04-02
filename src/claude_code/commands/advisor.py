"""
/advisor — configure the advisor model.

Migrated from: commands/advisor.ts
"""

from __future__ import annotations

import os
from collections.abc import Callable
from typing import Any

from claude_code.commands.base import Command, CommandContext, CommandResult
from claude_code.commands.spec import CommandSpec


def can_user_configure_advisor() -> bool:
    """Feature gate (ported from utils/advisor)."""
    return os.environ.get("DISABLE_ADVISOR_COMMAND", "").lower() not in ("1", "true", "yes")


def is_valid_advisor_model(_model: str) -> bool:
    """Stub until advisor allowlist is ported from utils/advisor."""
    return True


def model_supports_advisor(_main_model: str) -> bool:
    """Stub until model capability matrix is ported."""
    return True


async def advisor_local_call(
    args: str,
    get_app_state: Callable[[], Any],
    set_app_state: Callable[[Callable[[Any], Any]], None],
    parse_user_specified_model: Callable[[str], str] | None = None,
    normalize_model_string_for_api: Callable[[str], str] | None = None,
    validate_model: Callable[[str], Any] | None = None,
    get_default_main_loop_model: Callable[[], str] | None = None,
    update_user_settings: Callable[[dict[str, Any]], None] | None = None,
) -> dict[str, Any]:
    """Return LocalCommandResult-shaped dict (type/text)."""
    arg = args.strip().lower()
    pum = parse_user_specified_model or (lambda s: s)
    norm = normalize_model_string_for_api or (lambda s: s)
    default_model = get_default_main_loop_model() if get_default_main_loop_model else "claude-3-5-sonnet-latest"
    base_model = pum(getattr(get_app_state(), "main_loop_model", None) or default_model)

    if not arg:
        current = getattr(get_app_state(), "advisor_model", None)
        if not current:
            return {
                "type": "text",
                "value": ('Advisor: not set\nUse "/advisor <model>" to enable (e.g. "/advisor opus").'),
            }
        if not model_supports_advisor(base_model):
            return {
                "type": "text",
                "value": (
                    f"Advisor: {current} (inactive)\nThe current model ({base_model}) does not support advisors."
                ),
            }
        return {
            "type": "text",
            "value": (f'Advisor: {current}\nUse "/advisor unset" to disable or "/advisor <model>" to change.'),
        }

    if arg in ("unset", "off"):
        prev = getattr(get_app_state(), "advisor_model", None)

        def _clear(prev_state: Any) -> Any:
            if getattr(prev_state, "advisor_model", None) is None:
                return prev_state
            from dataclasses import replace

            if hasattr(prev_state, "__dataclass_fields__"):
                return replace(prev_state, advisor_model=None)
            ns = dict(vars(prev_state)) if hasattr(prev_state, "__dict__") else {}
            ns["advisor_model"] = None
            return type(prev_state)(**ns) if hasattr(prev_state, "__class__") else prev_state

        set_app_state(_clear)
        if update_user_settings:
            update_user_settings({"advisor_model": None})
        return {
            "type": "text",
            "value": (f"Advisor disabled (was {prev})." if prev else "Advisor already unset."),
        }

    normalized_model = norm(arg)
    resolved_model = pum(arg)
    if validate_model is not None:
        import inspect

        vr = validate_model(resolved_model)
        if inspect.isawaitable(vr):
            vr = await vr
        if hasattr(vr, "valid") and not vr.valid:
            err = getattr(vr, "error", None) or "unknown error"
            return {"type": "text", "value": f"Invalid advisor model: {err}"}

    if not is_valid_advisor_model(resolved_model):
        return {
            "type": "text",
            "value": f"The model {arg} ({resolved_model}) cannot be used as an advisor",
        }

    def _set(prev_state: Any) -> Any:
        if getattr(prev_state, "advisor_model", None) == normalized_model:
            return prev_state
        from dataclasses import replace

        if hasattr(prev_state, "__dataclass_fields__"):
            return replace(prev_state, advisor_model=normalized_model)
        ns = dict(vars(prev_state)) if hasattr(prev_state, "__dict__") else {}
        ns["advisor_model"] = normalized_model
        return type(prev_state)(**ns) if hasattr(prev_state, "__class__") else prev_state

    set_app_state(_set)
    if update_user_settings:
        update_user_settings({"advisor_model": normalized_model})

    if not model_supports_advisor(base_model):
        return {
            "type": "text",
            "value": (
                f"Advisor set to {normalized_model}.\n"
                f"Note: Your current model ({base_model}) does not support advisors. "
                "Switch to a supported model to use the advisor."
            ),
        }

    return {"type": "text", "value": f"Advisor set to {normalized_model}."}


ADVISOR_COMMAND_SPEC = CommandSpec(
    type="local",
    name="advisor",
    description="Configure the advisor model",
    argument_hint="[<model>|off]",
    supports_non_interactive=True,
    is_enabled=can_user_configure_advisor,
    is_hidden_fn=lambda: not can_user_configure_advisor(),
)


class AdvisorCommand(Command):
    """Registerable /advisor command."""

    async def execute(self, context: CommandContext) -> CommandResult:
        if not can_user_configure_advisor():
            return CommandResult(success=False, error="Advisor command disabled")
        get_state = context.get_app_state
        set_state = context.set_app_state
        if get_state is None or set_state is None:
            return CommandResult(success=False, error="App state not available")

        def _functional_set(updater: Callable[[Any], Any]) -> None:
            set_state(updater(get_state()))

        raw = " ".join(context.args).strip()
        out = await advisor_local_call(raw, get_state, _functional_set)
        return CommandResult(success=True, message=out.get("value"), output=out)


__all__ = [
    "ADVISOR_COMMAND_SPEC",
    "AdvisorCommand",
    "advisor_local_call",
    "can_user_configure_advisor",
]
