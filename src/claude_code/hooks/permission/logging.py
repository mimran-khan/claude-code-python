"""Permission decision logging."""

from dataclasses import dataclass

from ...services.analytics import log_event


@dataclass
class PermissionDecisionArgs:
    """Arguments for logging permission decisions."""

    tool_name: str
    tool_use_id: str
    decision: str  # "allow", "deny"
    source: str  # "hook", "user", "classifier"
    reason: str | None = None
    permanent: bool = False
    input_summary: str | None = None


def log_permission_decision(args: PermissionDecisionArgs) -> None:
    """Log a permission decision for analytics."""
    log_event(
        "tengu_permission_decision",
        {
            "tool_name": args.tool_name,
            "decision": args.decision,
            "source": args.source,
            "permanent": args.permanent,
        },
    )
