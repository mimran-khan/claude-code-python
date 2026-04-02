"""
Migration runner.

Execute and track migrations.

Migrated from: migrations/*.ts (common patterns)
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from ..utils.config_utils import get_claude_config_dir
from ..utils.debug import log_for_debugging


@dataclass
class Migration:
    """A migration to run."""

    name: str
    description: str
    run: Callable[[], bool]
    version: int = 1


@dataclass
class MigrationStatus:
    """Status of migrations."""

    completed: list[str] = field(default_factory=list)
    failed: list[str] = field(default_factory=list)
    pending: list[str] = field(default_factory=list)


class MigrationRunner:
    """
    Runner for executing migrations.
    """

    def __init__(self):
        self._migrations: list[Migration] = []
        self._status_file = Path(get_claude_config_dir()) / "migrations.json"

    def register(self, migration: Migration) -> None:
        """
        Register a migration.

        Args:
            migration: Migration to register
        """
        self._migrations.append(migration)

    def _load_status(self) -> dict[str, list[str]]:
        """Load migration status from disk."""
        if self._status_file.exists():
            try:
                with open(self._status_file) as f:
                    return json.load(f)
            except (OSError, json.JSONDecodeError):
                pass
        return {"completed": [], "failed": []}

    def _save_status(self, status: dict[str, list[str]]) -> None:
        """Save migration status to disk."""
        try:
            self._status_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self._status_file, "w") as f:
                json.dump(status, f, indent=2)
        except OSError:
            pass

    def run_all(self) -> MigrationStatus:
        """
        Run all pending migrations.

        Returns:
            MigrationStatus with results
        """
        status = self._load_status()
        completed = set(status.get("completed", []))
        failed = set(status.get("failed", []))

        result = MigrationStatus(
            completed=list(completed),
            failed=list(failed),
        )

        ordered = sorted(self._migrations, key=lambda m: (m.version, m.name))
        for migration in ordered:
            if migration.name in completed:
                continue

            result.pending.append(migration.name)

            try:
                log_for_debugging(f"migration: running {migration.name}")
                success = migration.run()

                if success:
                    completed.add(migration.name)
                    result.completed.append(migration.name)
                    result.pending.remove(migration.name)
                else:
                    failed.add(migration.name)
                    result.failed.append(migration.name)
                    result.pending.remove(migration.name)

            except Exception as e:
                log_for_debugging(f"migration: {migration.name} failed: {e}")
                failed.add(migration.name)
                result.failed.append(migration.name)
                if migration.name in result.pending:
                    result.pending.remove(migration.name)

        # Save status
        self._save_status(
            {
                "completed": list(completed),
                "failed": list(failed),
            }
        )

        return result

    def get_status(self) -> MigrationStatus:
        """Get current migration status."""
        status = self._load_status()
        completed = set(status.get("completed", []))
        failed = set(status.get("failed", []))

        ordered = sorted(self._migrations, key=lambda m: (m.version, m.name))
        pending = [m.name for m in ordered if m.name not in completed and m.name not in failed]

        return MigrationStatus(
            completed=list(completed),
            failed=list(failed),
            pending=pending,
        )


# Global runner
_runner: MigrationRunner | None = None


def get_migration_runner() -> MigrationRunner:
    """Get the global migration runner."""
    global _runner
    if _runner is None:
        _runner = MigrationRunner()
    return _runner


def run_migrations() -> MigrationStatus:
    """Run all pending migrations."""
    return get_migration_runner().run_all()


def get_migration_status() -> MigrationStatus:
    """Get current migration status."""
    return get_migration_runner().get_status()
