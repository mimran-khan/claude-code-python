"""
Web fetch helpers, caching hooks, and domain errors.

Migrated from: tools/WebFetchTool/utils.ts (errors + structure; HTTP in host).
"""

from __future__ import annotations


class DomainBlockedError(Exception):
    def __init__(self, domain: str) -> None:
        super().__init__(f"Claude Code is unable to fetch from {domain}")
        self.domain = domain


class DomainCheckFailedError(Exception):
    def __init__(self, domain: str) -> None:
        super().__init__(
            f"Unable to verify if domain {domain} is safe to fetch. "
            "This may be due to network restrictions or enterprise security policies.",
        )
        self.domain = domain


class EgressBlockedError(Exception):
    def __init__(self, domain: str) -> None:
        self.domain = domain
        super().__init__(
            '{"error_type":"EGRESS_BLOCKED","domain":"' + domain + '","message":"Access blocked by egress proxy."}',
        )


__all__ = ["DomainBlockedError", "DomainCheckFailedError", "EgressBlockedError"]
