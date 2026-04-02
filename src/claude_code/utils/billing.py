"""Python package-layout sibling for ``utils/billing.ts``.

The TypeScript tree is authoritative for the Node/Ink CLI; this module
exists so Python imports can mirror ``utils/`` paths. Implementations may live in other ``claude_code`` modules — search the codebase for related symbols.
"""

from __future__ import annotations

_mock_billing_access_override: bool | None = None


def set_mock_billing_access_override(value: bool | None) -> None:
    """Ant-only test hook mirrored from ``setMockBillingAccessOverride``."""
    global _mock_billing_access_override
    _mock_billing_access_override = value


def get_mock_billing_access_override() -> bool | None:
    return _mock_billing_access_override
