"""Shared helpers used by multiple tools (git metrics, teammate spawn types)."""

from .git_operation_tracking import (
    GitBranchInfo,
    GitCommitInfo,
    GitOperationDetectResult,
    GitPrInfo,
    GitPushInfo,
    detect_git_operation,
    parse_git_commit_id,
    parse_git_push_branch,
    track_git_operations,
)
from .spawn_multi_agent import (
    SpawnOutput,
    SpawnTeammateConfig,
    generate_unique_teammate_name,
    get_default_teammate_model,
    resolve_teammate_model,
    spawn_teammate,
)

__all__ = [
    "GitBranchInfo",
    "GitCommitInfo",
    "GitOperationDetectResult",
    "GitPrInfo",
    "GitPushInfo",
    "SpawnOutput",
    "SpawnTeammateConfig",
    "detect_git_operation",
    "generate_unique_teammate_name",
    "get_default_teammate_model",
    "parse_git_commit_id",
    "parse_git_push_branch",
    "resolve_teammate_model",
    "spawn_teammate",
    "track_git_operations",
]
