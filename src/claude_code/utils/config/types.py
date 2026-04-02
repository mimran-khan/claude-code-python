"""Dataclass mirrors for JSON config documents."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

BillingType = str | None


@dataclass
class AccountInfo:
    account_uuid: str = ""
    email_address: str = ""
    organization_uuid: str | None = None
    organization_name: str | None = None
    organization_role: str | None = None
    workspace_role: str | None = None
    display_name: str | None = None
    has_extra_usage_enabled: bool | None = None
    billing_type: BillingType = None
    account_created_at: str | None = None
    subscription_created_at: str | None = None


@dataclass
class ProjectConfigLite:
    allowed_tools: list[str] = field(default_factory=list)
    mcp_context_uris: list[str] = field(default_factory=list)
    mcp_servers: dict[str, Any] = field(default_factory=dict)
    has_trust_dialog_accepted: bool = False
    project_onboarding_seen_count: int = 0


InstallMethod = Literal["local", "native", "global", "unknown"]


@dataclass
class GlobalConfigLite:
    num_startups: int = 0
    theme: str = "dark"
    install_method: InstallMethod | None = None
    projects: dict[str, ProjectConfigLite] = field(default_factory=dict)
    oauth_account: AccountInfo | None = None
    client_data_cache: dict[str, str] | None = None
