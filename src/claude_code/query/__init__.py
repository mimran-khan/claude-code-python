"""
Query processing and token budget management.

Migrated from: query/*.ts
"""

from .config import (
    QueryConfig,
    get_default_query_config,
)
from .deps import (
    QueryDeps,
    create_query_deps,
)
from .stop_hooks import (
    StopReason,
    should_stop_query,
)
from .token_budget import (
    BudgetTracker,
    TokenBudgetDecision,
    check_token_budget,
    create_budget_tracker,
)

__all__ = [
    # Token budget
    "BudgetTracker",
    "TokenBudgetDecision",
    "create_budget_tracker",
    "check_token_budget",
    # Config
    "QueryConfig",
    "get_default_query_config",
    # Stop hooks
    "StopReason",
    "should_stop_query",
    # Dependencies
    "QueryDeps",
    "create_query_deps",
]
