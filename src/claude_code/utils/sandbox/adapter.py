"""
Sandbox adapter: path resolution and settings → runtime config dict.

Full ``SandboxManager`` parity requires a native sandbox runtime; this module
ports the pure settings / path logic from ``sandbox-adapter.ts``.

Migrated from: utils/sandbox/sandbox-adapter.ts (partial)
"""

from __future__ import annotations

import os
import re
import tempfile
from typing import Any

from ...bootstrap.state import (
    get_additional_directories_for_claude_md,
    get_original_cwd,
)
from ...constants.tools import (
    FILE_EDIT_TOOL_NAME,
    FILE_READ_TOOL_NAME,
    WEB_FETCH_TOOL_NAME,
)
from ..cwd import get_cwd
from ..path_utils import expand_path
from ..ripgrep import ripgrep_command
from ..settings.constants import SETTING_SOURCES, SettingSource
from ..settings.managed_path import get_managed_settings_drop_in_dir
from ..settings.settings import (
    get_settings_file_path_for_source,
    get_settings_for_source,
    get_settings_root_path_for_source,
    update_settings_for_source,
)

BASH_TOOL_NAME = "Bash"


def permission_rule_value_from_string(rule_string: str) -> dict[str, str | None]:
    m = re.match(r"^([^(]+)\(([^)]+)\)$", rule_string)
    if not m:
        return {"toolName": rule_string, "ruleContent": None}
    return {"toolName": m.group(1), "ruleContent": m.group(2)}


def permission_rule_extract_prefix(permission_rule: str) -> str | None:
    m = re.match(r"^(.+):\*$", permission_rule)
    return m.group(1) if m else None


def resolve_path_pattern_for_sandbox(pattern: str, source: SettingSource) -> str:
    if pattern.startswith("//"):
        return pattern[1:]
    if pattern.startswith("/") and not pattern.startswith("//"):
        root = get_settings_root_path_for_source(source)
        if root is None:
            return pattern
        return os.path.join(root, pattern[1:].lstrip(os.sep))
    return pattern


def resolve_sandbox_filesystem_path(pattern: str, source: SettingSource) -> str:
    if pattern.startswith("//"):
        return pattern[1:]
    root = get_settings_root_path_for_source(source)
    return expand_path(pattern, root)


def should_allow_managed_sandbox_domains_only() -> bool:
    pol = get_settings_for_source("policySettings") or {}
    sandbox = pol.get("sandbox") or {}
    network = sandbox.get("network") or {}
    return network.get("allowManagedDomainsOnly") is True


def _should_allow_managed_read_paths_only() -> bool:
    pol = get_settings_for_source("policySettings") or {}
    fs = (pol.get("sandbox") or {}).get("filesystem") or {}
    return fs.get("allowManagedReadPathsOnly") is True


def convert_to_sandbox_runtime_config(settings: dict[str, Any]) -> dict[str, Any]:
    permissions = settings.get("permissions") or {}
    allowed_domains: list[str] = []
    denied_domains: list[str] = []

    if should_allow_managed_sandbox_domains_only():
        policy = get_settings_for_source("policySettings") or {}
        p_sandbox = policy.get("sandbox") or {}
        p_net = p_sandbox.get("network") or {}
        for d in p_net.get("allowedDomains") or []:
            allowed_domains.append(str(d))
        for rule_string in (policy.get("permissions") or {}).get("allow") or []:
            rule = permission_rule_value_from_string(str(rule_string))
            if rule["toolName"] == WEB_FETCH_TOOL_NAME and rule.get("ruleContent"):
                rc = str(rule["ruleContent"])
                if rc.startswith("domain:"):
                    allowed_domains.append(rc[len("domain:") :])
    else:
        s_sandbox = settings.get("sandbox") or {}
        for d in (s_sandbox.get("network") or {}).get("allowedDomains") or []:
            allowed_domains.append(str(d))
        for rule_string in permissions.get("allow") or []:
            rule = permission_rule_value_from_string(str(rule_string))
            if rule["toolName"] == WEB_FETCH_TOOL_NAME and rule.get("ruleContent"):
                rc = str(rule["ruleContent"])
                if rc.startswith("domain:"):
                    allowed_domains.append(rc[len("domain:") :])

    for rule_string in permissions.get("deny") or []:
        rule = permission_rule_value_from_string(str(rule_string))
        if rule["toolName"] == WEB_FETCH_TOOL_NAME and rule.get("ruleContent"):
            rc = str(rule["ruleContent"])
            if rc.startswith("domain:"):
                denied_domains.append(rc[len("domain:") :])

    claude_tmp = os.path.join(tempfile.gettempdir(), "claude-code")
    allow_write: list[str] = [".", claude_tmp]
    deny_write: list[str] = []
    deny_read: list[str] = []
    allow_read: list[str] = []

    for src in SETTING_SOURCES:
        pth = get_settings_file_path_for_source(src)
        if pth:
            deny_write.append(pth)
    deny_write.append(get_managed_settings_drop_in_dir())

    cwd = get_cwd()
    orig = get_original_cwd()
    if cwd != orig:
        deny_write.append(os.path.join(cwd, ".claude", "settings.json"))
        deny_write.append(os.path.join(cwd, ".claude", "settings.local.json"))

    deny_write.append(os.path.join(orig, ".claude", "skills"))
    if cwd != orig:
        deny_write.append(os.path.join(cwd, ".claude", "skills"))

    extra_dirs = set(permissions.get("additionalDirectories") or [])
    extra_dirs.update(get_additional_directories_for_claude_md())
    allow_write.extend(str(d) for d in extra_dirs)

    for source in SETTING_SOURCES:
        src_settings = get_settings_for_source(source) or {}
        perms = src_settings.get("permissions") or {}
        for rule_string in perms.get("allow") or []:
            rule = permission_rule_value_from_string(str(rule_string))
            if rule["toolName"] == FILE_EDIT_TOOL_NAME and rule.get("ruleContent"):
                allow_write.append(resolve_path_pattern_for_sandbox(str(rule["ruleContent"]), source))
        for rule_string in perms.get("deny") or []:
            rule = permission_rule_value_from_string(str(rule_string))
            if rule["toolName"] == FILE_EDIT_TOOL_NAME and rule.get("ruleContent"):
                deny_write.append(resolve_path_pattern_for_sandbox(str(rule["ruleContent"]), source))
            if rule["toolName"] == FILE_READ_TOOL_NAME and rule.get("ruleContent"):
                deny_read.append(resolve_path_pattern_for_sandbox(str(rule["ruleContent"]), source))
        fs = (src_settings.get("sandbox") or {}).get("filesystem") or {}
        for p in fs.get("allowWrite") or []:
            allow_write.append(resolve_sandbox_filesystem_path(str(p), source))
        for p in fs.get("denyWrite") or []:
            deny_write.append(resolve_sandbox_filesystem_path(str(p), source))
        for p in fs.get("denyRead") or []:
            deny_read.append(resolve_sandbox_filesystem_path(str(p), source))
        if not _should_allow_managed_read_paths_only() or source == "policySettings":
            for p in fs.get("allowRead") or []:
                allow_read.append(resolve_sandbox_filesystem_path(str(p), source))

    rg_path, rg_args = ripgrep_command()
    ripgrep_cfg = (settings.get("sandbox") or {}).get("ripgrep") or {
        "command": rg_path,
        "args": rg_args,
        "argv0": None,
    }

    s_sandbox = settings.get("sandbox") or {}
    s_net = s_sandbox.get("network") or {}
    return {
        "network": {
            "allowedDomains": allowed_domains,
            "deniedDomains": denied_domains,
            "allowUnixSockets": s_net.get("allowUnixSockets"),
            "allowAllUnixSockets": s_net.get("allowAllUnixSockets"),
            "allowLocalBinding": s_net.get("allowLocalBinding"),
            "httpProxyPort": s_net.get("httpProxyPort"),
            "socksProxyPort": s_net.get("socksProxyPort"),
        },
        "filesystem": {
            "denyRead": deny_read,
            "allowRead": allow_read,
            "allowWrite": allow_write,
            "denyWrite": deny_write,
        },
        "ignoreViolations": s_sandbox.get("ignoreViolations"),
        "enableWeakerNestedSandbox": s_sandbox.get("enableWeakerNestedSandbox"),
        "enableWeakerNetworkIsolation": s_sandbox.get("enableWeakerNetworkIsolation"),
        "ripgrep": ripgrep_cfg,
    }


def add_to_excluded_commands(
    command: str,
    permission_updates: list[dict[str, Any]] | None = None,
) -> str:
    existing = get_settings_for_source("localSettings") or {}
    sandbox = existing.get("sandbox") or {}
    excluded: list[str] = list(sandbox.get("excludedCommands") or [])
    command_pattern = command
    if permission_updates:
        for upd in permission_updates:
            if upd.get("type") != "addRules":
                continue
            rules = upd.get("rules") or []
            if not any(r.get("toolName") == BASH_TOOL_NAME for r in rules):
                continue
            for r in rules:
                if r.get("toolName") != BASH_TOOL_NAME:
                    continue
                rc = r.get("ruleContent")
                if rc:
                    command_pattern = permission_rule_extract_prefix(str(rc)) or str(rc)
            break
    if command_pattern not in excluded:
        excluded.append(command_pattern)
        update_settings_for_source(
            "localSettings",
            {"sandbox": {**sandbox, "excludedCommands": excluded}},
        )
    return command_pattern


class SandboxManagerStub:
    """Placeholder for ``ISandboxManager`` until a Python sandbox-runtime exists."""

    async def initialize(self, *_: Any, **__: Any) -> None:
        return None

    def is_sandboxing_enabled(self) -> bool:
        return False

    async def reset(self) -> None:
        return None


SandboxManager = SandboxManagerStub()
