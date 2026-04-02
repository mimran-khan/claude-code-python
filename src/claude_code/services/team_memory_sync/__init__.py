"""Team memory sync. Migrated from: services/teamMemorySync/*.ts"""

from .secret_scanner import SecretMatch, get_secret_label, scan_for_secrets
from .sync import (
    create_sync_state,
    fetch_team_memory_once,
    is_team_memory_sync_available,
    pull_team_memory,
    push_team_memory,
    team_memory_endpoint,
)
from .team_mem_secret_guard import check_team_mem_secrets
from .types import (
    SkippedSecretFile,
    SyncState,
    TeamMemorySyncFetchResult,
    TeamMemorySyncPushResult,
)
from .watcher import (
    is_permanent_failure,
    notify_team_memory_write,
    start_team_memory_watcher,
    stop_team_memory_watcher,
)

__all__ = [
    "SyncState",
    "SkippedSecretFile",
    "TeamMemorySyncFetchResult",
    "TeamMemorySyncPushResult",
    "scan_for_secrets",
    "get_secret_label",
    "SecretMatch",
    "check_team_mem_secrets",
    "create_sync_state",
    "fetch_team_memory_once",
    "pull_team_memory",
    "push_team_memory",
    "is_team_memory_sync_available",
    "team_memory_endpoint",
    "is_permanent_failure",
    "start_team_memory_watcher",
    "notify_team_memory_write",
    "stop_team_memory_watcher",
]
