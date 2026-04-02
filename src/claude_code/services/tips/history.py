"""Tip history tracking."""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class TipShowRecord:
    """Record of when a tip was shown."""

    tip_id: str
    shown_at: datetime
    session_id: str | None = None


@dataclass
class TipHistory:
    """History of tip shows."""

    records: list[TipShowRecord] = field(default_factory=list)
    session_count: int = 0
    last_tip_session: int = 0


# Global history
_history = TipHistory()


def get_tip_history() -> TipHistory:
    """Get the tip history."""
    return _history


def get_sessions_since_last_shown(tip_id: str | None) -> int:
    """Get number of sessions since tip was last shown."""
    if tip_id is None:
        return _history.session_count - _history.last_tip_session

    for record in reversed(_history.records):
        if record.tip_id == tip_id:
            # Would need to track session number per record for accuracy
            return 0

    return _history.session_count


def get_show_count(tip_id: str) -> int:
    """Get how many times a tip has been shown."""
    return sum(1 for r in _history.records if r.tip_id == tip_id)


def record_tip_shown(tip_id: str, session_id: str | None = None) -> None:
    """Record that a tip was shown."""
    _history.records.append(
        TipShowRecord(
            tip_id=tip_id,
            shown_at=datetime.utcnow(),
            session_id=session_id,
        )
    )
    _history.last_tip_session = _history.session_count


def increment_session_count() -> None:
    """Increment the session count."""
    _history.session_count += 1


def clear_history() -> None:
    """Clear tip history (for testing)."""
    global _history
    _history = TipHistory()
