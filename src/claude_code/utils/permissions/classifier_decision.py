"""Classifier decision aggregation (``utils/permissions/classifierDecision.ts``)."""

from __future__ import annotations

from dataclasses import dataclass

from .classifier_shared import ClassifierLabel, ClassifierSignal


@dataclass
class ClassifierDecision:
    final_label: ClassifierLabel
    signals: list[ClassifierSignal]


def merge_signals(signals: list[ClassifierSignal]) -> ClassifierDecision:
    if not signals:
        return ClassifierDecision(final_label="ask", signals=[])
    order: dict[ClassifierLabel, int] = {"deny": 0, "ask": 1, "allow": 2, "unknown": 3}
    best = min(signals, key=lambda s: order.get(s.label, 9))
    return ClassifierDecision(final_label=best.label, signals=signals)
