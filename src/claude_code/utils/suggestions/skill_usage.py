"""
Skill usage tracking.

Track and score skill/command usage for suggestions.

Migrated from: utils/suggestions/skillUsageTracking.ts
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path

from ..config_utils import get_claude_config_dir


@dataclass
class SkillUsage:
    """Usage data for a skill."""

    name: str
    use_count: int = 0
    last_used: float = 0.0
    total_time_spent: float = 0.0


class SkillUsageTracker:
    """
    Track skill usage for suggestion ranking.
    """

    def __init__(self, storage_path: str | None = None):
        if storage_path:
            self._path = Path(storage_path)
        else:
            self._path = Path(get_claude_config_dir()) / "skill_usage.json"

        self._usage: dict[str, SkillUsage] = {}
        self._load()

    def _load(self) -> None:
        """Load usage data from file."""
        if self._path.exists():
            try:
                with open(self._path) as f:
                    data = json.load(f)

                for name, info in data.items():
                    self._usage[name] = SkillUsage(
                        name=name,
                        use_count=info.get("use_count", 0),
                        last_used=info.get("last_used", 0.0),
                        total_time_spent=info.get("total_time_spent", 0.0),
                    )
            except (OSError, json.JSONDecodeError):
                pass

    def _save(self) -> None:
        """Save usage data to file."""
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)

            data = {
                name: {
                    "use_count": usage.use_count,
                    "last_used": usage.last_used,
                    "total_time_spent": usage.total_time_spent,
                }
                for name, usage in self._usage.items()
            }

            with open(self._path, "w") as f:
                json.dump(data, f, indent=2)
        except OSError:
            pass

    def record_usage(
        self,
        skill_name: str,
        time_spent: float = 0.0,
    ) -> None:
        """
        Record skill usage.

        Args:
            skill_name: Skill name
            time_spent: Time spent using skill (seconds)
        """
        if skill_name not in self._usage:
            self._usage[skill_name] = SkillUsage(name=skill_name)

        usage = self._usage[skill_name]
        usage.use_count += 1
        usage.last_used = time.time()
        usage.total_time_spent += time_spent

        self._save()

    def get_score(self, skill_name: str) -> float:
        """
        Get usage score for ranking.

        Score combines frequency and recency.

        Args:
            skill_name: Skill name

        Returns:
            Score from 0 to 1
        """
        if skill_name not in self._usage:
            return 0.0

        usage = self._usage[skill_name]
        now = time.time()

        # Frequency score (log scale)
        freq_score = min(1.0, (usage.use_count / 100) ** 0.5)

        # Recency score (decay over 30 days)
        days_since_use = (now - usage.last_used) / (24 * 60 * 60)
        recency_score = max(0.0, 1.0 - (days_since_use / 30))

        # Combined score
        return (freq_score * 0.6) + (recency_score * 0.4)

    def get_all_scores(self) -> dict[str, float]:
        """Get scores for all tracked skills."""
        return {name: self.get_score(name) for name in self._usage}

    def get_frequently_used(self, limit: int = 10) -> list[str]:
        """Get most frequently used skills."""
        sorted_skills = sorted(
            self._usage.items(),
            key=lambda x: x[1].use_count,
            reverse=True,
        )
        return [name for name, _ in sorted_skills[:limit]]


# Global tracker
_tracker: SkillUsageTracker | None = None


def _get_tracker() -> SkillUsageTracker:
    """Get the global tracker."""
    global _tracker
    if _tracker is None:
        _tracker = SkillUsageTracker()
    return _tracker


def record_skill_usage(skill_name: str, time_spent: float = 0.0) -> None:
    """Record skill usage."""
    _get_tracker().record_usage(skill_name, time_spent)


def get_skill_usage_score(skill_name: str) -> float:
    """Get skill usage score."""
    return _get_tracker().get_score(skill_name)


def get_frequently_used_skills(limit: int = 10) -> list[str]:
    """Get frequently used skills."""
    return _get_tracker().get_frequently_used(limit)
