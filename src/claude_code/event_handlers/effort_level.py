"""
Model effort display (ported from commands/effort, ModelPicker, utils/effort.ts).

Replaces useMemo-derived effort labels with explicit resolution from model + settings.
"""

from __future__ import annotations

from dataclasses import dataclass

from claude_code.utils.effort import (
    EffortLevel,
    EffortValue,
    get_displayed_effort_level,
    resolve_applied_effort,
)


@dataclass
class EffortLevelHandler:
    model: str
    app_state_effort: EffortValue | None = None

    @property
    def applied(self) -> EffortValue | None:
        return resolve_applied_effort(self.model, self.app_state_effort)

    @property
    def displayed_level(self) -> EffortLevel:
        return get_displayed_effort_level(self.model, self.app_state_effort)
