"""
Claude Code internal analytics event (Statsig / first-party logging).

Migrated from: types/generated/events_mono/claude_code/v1/claude_code_internal_event.ts
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from ....google.protobuf.timestamp import datetime_to_iso_z, parse_flexible_timestamp
from ...common.v1.auth import (
    PublicApiAuth,
    public_api_auth_from_json,
    public_api_auth_from_partial,
    public_api_auth_to_json,
)


def _is_set(value: Any) -> bool:
    return value is not None


@dataclass
class GitHubActionsMetadata:
    actor_id: str = ""
    repository_id: str = ""
    repository_owner_id: str = ""


def github_actions_metadata_from_json(obj: Any) -> GitHubActionsMetadata:
    if not isinstance(obj, dict):
        return GitHubActionsMetadata()
    return GitHubActionsMetadata(
        actor_id=str(obj["actor_id"]) if _is_set(obj.get("actor_id")) else "",
        repository_id=str(obj["repository_id"]) if _is_set(obj.get("repository_id")) else "",
        repository_owner_id=str(obj["repository_owner_id"]) if _is_set(obj.get("repository_owner_id")) else "",
    )


def github_actions_metadata_to_json(message: GitHubActionsMetadata) -> dict[str, Any]:
    obj: dict[str, Any] = {}
    if message.actor_id:
        obj["actor_id"] = message.actor_id
    if message.repository_id:
        obj["repository_id"] = message.repository_id
    if message.repository_owner_id:
        obj["repository_owner_id"] = message.repository_owner_id
    return obj


def github_actions_metadata_from_partial(obj: Any) -> GitHubActionsMetadata:
    if not isinstance(obj, dict):
        return GitHubActionsMetadata()
    return GitHubActionsMetadata(
        actor_id=str(obj.get("actor_id", "") or ""),
        repository_id=str(obj.get("repository_id", "") or ""),
        repository_owner_id=str(obj.get("repository_owner_id", "") or ""),
    )


@dataclass
class EnvironmentMetadata:
    platform: str = ""
    node_version: str = ""
    terminal: str = ""
    package_managers: str = ""
    runtimes: str = ""
    is_running_with_bun: bool = False
    is_ci: bool = False
    is_claubbit: bool = False
    is_github_action: bool = False
    is_claude_code_action: bool = False
    is_claude_ai_auth: bool = False
    version: str = ""
    github_event_name: str = ""
    github_actions_runner_environment: str = ""
    github_actions_runner_os: str = ""
    github_action_ref: str = ""
    wsl_version: str = ""
    github_actions_metadata: GitHubActionsMetadata | None = None
    arch: str = ""
    is_claude_code_remote: bool = False
    remote_environment_type: str = ""
    claude_code_container_id: str = ""
    claude_code_remote_session_id: str = ""
    tags: list[str] = field(default_factory=list)
    deployment_environment: str = ""
    is_conductor: bool = False
    version_base: str = ""
    coworker_type: str = ""
    build_time: str = ""
    is_local_agent_mode: bool = False
    linux_distro_id: str = ""
    linux_distro_version: str = ""
    linux_kernel: str = ""
    vcs: str = ""
    platform_raw: str = ""


def environment_metadata_from_json(obj: Any) -> EnvironmentMetadata:
    if not isinstance(obj, dict):
        return EnvironmentMetadata()
    gh_raw = obj.get("github_actions_metadata")
    tags_val = obj.get("tags")
    tag_list: list[str] = []
    if isinstance(tags_val, list):
        tag_list = [str(x) for x in tags_val]
    return EnvironmentMetadata(
        platform=str(obj["platform"]) if _is_set(obj.get("platform")) else "",
        node_version=str(obj["node_version"]) if _is_set(obj.get("node_version")) else "",
        terminal=str(obj["terminal"]) if _is_set(obj.get("terminal")) else "",
        package_managers=str(obj["package_managers"]) if _is_set(obj.get("package_managers")) else "",
        runtimes=str(obj["runtimes"]) if _is_set(obj.get("runtimes")) else "",
        is_running_with_bun=bool(obj["is_running_with_bun"]) if _is_set(obj.get("is_running_with_bun")) else False,
        is_ci=bool(obj["is_ci"]) if _is_set(obj.get("is_ci")) else False,
        is_claubbit=bool(obj["is_claubbit"]) if _is_set(obj.get("is_claubbit")) else False,
        is_github_action=bool(obj["is_github_action"]) if _is_set(obj.get("is_github_action")) else False,
        is_claude_code_action=bool(obj["is_claude_code_action"])
        if _is_set(obj.get("is_claude_code_action"))
        else False,
        is_claude_ai_auth=bool(obj["is_claude_ai_auth"]) if _is_set(obj.get("is_claude_ai_auth")) else False,
        version=str(obj["version"]) if _is_set(obj.get("version")) else "",
        github_event_name=str(obj["github_event_name"]) if _is_set(obj.get("github_event_name")) else "",
        github_actions_runner_environment=str(obj["github_actions_runner_environment"])
        if _is_set(obj.get("github_actions_runner_environment"))
        else "",
        github_actions_runner_os=str(obj["github_actions_runner_os"])
        if _is_set(obj.get("github_actions_runner_os"))
        else "",
        github_action_ref=str(obj["github_action_ref"]) if _is_set(obj.get("github_action_ref")) else "",
        wsl_version=str(obj["wsl_version"]) if _is_set(obj.get("wsl_version")) else "",
        github_actions_metadata=github_actions_metadata_from_json(gh_raw) if _is_set(gh_raw) else None,
        arch=str(obj["arch"]) if _is_set(obj.get("arch")) else "",
        is_claude_code_remote=bool(obj["is_claude_code_remote"])
        if _is_set(obj.get("is_claude_code_remote"))
        else False,
        remote_environment_type=str(obj["remote_environment_type"])
        if _is_set(obj.get("remote_environment_type"))
        else "",
        claude_code_container_id=str(obj["claude_code_container_id"])
        if _is_set(obj.get("claude_code_container_id"))
        else "",
        claude_code_remote_session_id=str(obj["claude_code_remote_session_id"])
        if _is_set(obj.get("claude_code_remote_session_id"))
        else "",
        tags=tag_list,
        deployment_environment=str(obj["deployment_environment"]) if _is_set(obj.get("deployment_environment")) else "",
        is_conductor=bool(obj["is_conductor"]) if _is_set(obj.get("is_conductor")) else False,
        version_base=str(obj["version_base"]) if _is_set(obj.get("version_base")) else "",
        coworker_type=str(obj["coworker_type"]) if _is_set(obj.get("coworker_type")) else "",
        build_time=str(obj["build_time"]) if _is_set(obj.get("build_time")) else "",
        is_local_agent_mode=bool(obj["is_local_agent_mode"]) if _is_set(obj.get("is_local_agent_mode")) else False,
        linux_distro_id=str(obj["linux_distro_id"]) if _is_set(obj.get("linux_distro_id")) else "",
        linux_distro_version=str(obj["linux_distro_version"]) if _is_set(obj.get("linux_distro_version")) else "",
        linux_kernel=str(obj["linux_kernel"]) if _is_set(obj.get("linux_kernel")) else "",
        vcs=str(obj["vcs"]) if _is_set(obj.get("vcs")) else "",
        platform_raw=str(obj["platform_raw"]) if _is_set(obj.get("platform_raw")) else "",
    )


def environment_metadata_to_json(message: EnvironmentMetadata) -> dict[str, Any]:
    obj: dict[str, Any] = {}
    if message.platform:
        obj["platform"] = message.platform
    if message.node_version:
        obj["node_version"] = message.node_version
    if message.terminal:
        obj["terminal"] = message.terminal
    if message.package_managers:
        obj["package_managers"] = message.package_managers
    if message.runtimes:
        obj["runtimes"] = message.runtimes
    if message.is_running_with_bun:
        obj["is_running_with_bun"] = message.is_running_with_bun
    if message.is_ci:
        obj["is_ci"] = message.is_ci
    if message.is_claubbit:
        obj["is_claubbit"] = message.is_claubbit
    if message.is_github_action:
        obj["is_github_action"] = message.is_github_action
    if message.is_claude_code_action:
        obj["is_claude_code_action"] = message.is_claude_code_action
    if message.is_claude_ai_auth:
        obj["is_claude_ai_auth"] = message.is_claude_ai_auth
    if message.version:
        obj["version"] = message.version
    if message.github_event_name:
        obj["github_event_name"] = message.github_event_name
    if message.github_actions_runner_environment:
        obj["github_actions_runner_environment"] = message.github_actions_runner_environment
    if message.github_actions_runner_os:
        obj["github_actions_runner_os"] = message.github_actions_runner_os
    if message.github_action_ref:
        obj["github_action_ref"] = message.github_action_ref
    if message.wsl_version:
        obj["wsl_version"] = message.wsl_version
    if message.github_actions_metadata is not None:
        obj["github_actions_metadata"] = github_actions_metadata_to_json(message.github_actions_metadata)
    if message.arch:
        obj["arch"] = message.arch
    if message.is_claude_code_remote:
        obj["is_claude_code_remote"] = message.is_claude_code_remote
    if message.remote_environment_type:
        obj["remote_environment_type"] = message.remote_environment_type
    if message.claude_code_container_id:
        obj["claude_code_container_id"] = message.claude_code_container_id
    if message.claude_code_remote_session_id:
        obj["claude_code_remote_session_id"] = message.claude_code_remote_session_id
    if message.tags:
        obj["tags"] = list(message.tags)
    if message.deployment_environment:
        obj["deployment_environment"] = message.deployment_environment
    if message.is_conductor:
        obj["is_conductor"] = message.is_conductor
    if message.version_base:
        obj["version_base"] = message.version_base
    if message.coworker_type:
        obj["coworker_type"] = message.coworker_type
    if message.build_time:
        obj["build_time"] = message.build_time
    if message.is_local_agent_mode:
        obj["is_local_agent_mode"] = message.is_local_agent_mode
    if message.linux_distro_id:
        obj["linux_distro_id"] = message.linux_distro_id
    if message.linux_distro_version:
        obj["linux_distro_version"] = message.linux_distro_version
    if message.linux_kernel:
        obj["linux_kernel"] = message.linux_kernel
    if message.vcs:
        obj["vcs"] = message.vcs
    if message.platform_raw:
        obj["platform_raw"] = message.platform_raw
    return obj


def environment_metadata_from_partial(obj: Any) -> EnvironmentMetadata:
    if not isinstance(obj, dict):
        return EnvironmentMetadata()
    gh_raw = obj.get("github_actions_metadata")
    tags_val = obj.get("tags")
    tag_list: list[str] = []
    if isinstance(tags_val, list):
        tag_list = [str(x) for x in tags_val]
    return EnvironmentMetadata(
        platform=str(obj.get("platform", "") or ""),
        node_version=str(obj.get("node_version", "") or ""),
        terminal=str(obj.get("terminal", "") or ""),
        package_managers=str(obj.get("package_managers", "") or ""),
        runtimes=str(obj.get("runtimes", "") or ""),
        is_running_with_bun=bool(obj.get("is_running_with_bun", False)),
        is_ci=bool(obj.get("is_ci", False)),
        is_claubbit=bool(obj.get("is_claubbit", False)),
        is_github_action=bool(obj.get("is_github_action", False)),
        is_claude_code_action=bool(obj.get("is_claude_code_action", False)),
        is_claude_ai_auth=bool(obj.get("is_claude_ai_auth", False)),
        version=str(obj.get("version", "") or ""),
        github_event_name=str(obj.get("github_event_name", "") or ""),
        github_actions_runner_environment=str(obj.get("github_actions_runner_environment", "") or ""),
        github_actions_runner_os=str(obj.get("github_actions_runner_os", "") or ""),
        github_action_ref=str(obj.get("github_action_ref", "") or ""),
        wsl_version=str(obj.get("wsl_version", "") or ""),
        github_actions_metadata=github_actions_metadata_from_partial(gh_raw) if isinstance(gh_raw, dict) else None,
        arch=str(obj.get("arch", "") or ""),
        is_claude_code_remote=bool(obj.get("is_claude_code_remote", False)),
        remote_environment_type=str(obj.get("remote_environment_type", "") or ""),
        claude_code_container_id=str(obj.get("claude_code_container_id", "") or ""),
        claude_code_remote_session_id=str(obj.get("claude_code_remote_session_id", "") or ""),
        tags=tag_list,
        deployment_environment=str(obj.get("deployment_environment", "") or ""),
        is_conductor=bool(obj.get("is_conductor", False)),
        version_base=str(obj.get("version_base", "") or ""),
        coworker_type=str(obj.get("coworker_type", "") or ""),
        build_time=str(obj.get("build_time", "") or ""),
        is_local_agent_mode=bool(obj.get("is_local_agent_mode", False)),
        linux_distro_id=str(obj.get("linux_distro_id", "") or ""),
        linux_distro_version=str(obj.get("linux_distro_version", "") or ""),
        linux_kernel=str(obj.get("linux_kernel", "") or ""),
        vcs=str(obj.get("vcs", "") or ""),
        platform_raw=str(obj.get("platform_raw", "") or ""),
    )


@dataclass
class SlackContext:
    slack_team_id: str = ""
    is_enterprise_install: bool = False
    trigger: str = ""
    creation_method: str = ""


def slack_context_from_json(obj: Any) -> SlackContext:
    if not isinstance(obj, dict):
        return SlackContext()
    return SlackContext(
        slack_team_id=str(obj["slack_team_id"]) if _is_set(obj.get("slack_team_id")) else "",
        is_enterprise_install=bool(obj["is_enterprise_install"])
        if _is_set(obj.get("is_enterprise_install"))
        else False,
        trigger=str(obj["trigger"]) if _is_set(obj.get("trigger")) else "",
        creation_method=str(obj["creation_method"]) if _is_set(obj.get("creation_method")) else "",
    )


def slack_context_to_json(message: SlackContext) -> dict[str, Any]:
    obj: dict[str, Any] = {}
    if message.slack_team_id:
        obj["slack_team_id"] = message.slack_team_id
    if message.is_enterprise_install:
        obj["is_enterprise_install"] = message.is_enterprise_install
    if message.trigger:
        obj["trigger"] = message.trigger
    if message.creation_method:
        obj["creation_method"] = message.creation_method
    return obj


def slack_context_from_partial(obj: Any) -> SlackContext:
    if not isinstance(obj, dict):
        return SlackContext()
    return SlackContext(
        slack_team_id=str(obj.get("slack_team_id", "") or ""),
        is_enterprise_install=bool(obj.get("is_enterprise_install", False)),
        trigger=str(obj.get("trigger", "") or ""),
        creation_method=str(obj.get("creation_method", "") or ""),
    )


@dataclass
class ClaudeCodeInternalEvent:
    event_name: str = ""
    client_timestamp: datetime | None = None
    model: str = ""
    session_id: str = ""
    user_type: str = ""
    betas: str = ""
    env: EnvironmentMetadata | None = None
    entrypoint: str = ""
    agent_sdk_version: str = ""
    is_interactive: bool = False
    client_type: str = ""
    process: str = ""
    additional_metadata: str = ""
    auth: PublicApiAuth | None = None
    server_timestamp: datetime | None = None
    event_id: str = ""
    device_id: str = ""
    swe_bench_run_id: str = ""
    swe_bench_instance_id: str = ""
    swe_bench_task_id: str = ""
    email: str = ""
    agent_id: str = ""
    parent_session_id: str = ""
    agent_type: str = ""
    slack: SlackContext | None = None
    team_name: str = ""
    skill_name: str = ""
    plugin_name: str = ""
    marketplace_name: str = ""


def claude_code_internal_event_from_json(obj: Any) -> ClaudeCodeInternalEvent:
    if not isinstance(obj, dict):
        return ClaudeCodeInternalEvent()
    ct_raw = obj.get("client_timestamp")
    st_raw = obj.get("server_timestamp")
    env_raw = obj.get("env")
    auth_raw = obj.get("auth")
    slack_raw = obj.get("slack")
    return ClaudeCodeInternalEvent(
        event_name=str(obj["event_name"]) if _is_set(obj.get("event_name")) else "",
        client_timestamp=parse_flexible_timestamp(ct_raw) if _is_set(ct_raw) else None,
        model=str(obj["model"]) if _is_set(obj.get("model")) else "",
        session_id=str(obj["session_id"]) if _is_set(obj.get("session_id")) else "",
        user_type=str(obj["user_type"]) if _is_set(obj.get("user_type")) else "",
        betas=str(obj["betas"]) if _is_set(obj.get("betas")) else "",
        env=environment_metadata_from_json(env_raw) if _is_set(env_raw) else None,
        entrypoint=str(obj["entrypoint"]) if _is_set(obj.get("entrypoint")) else "",
        agent_sdk_version=str(obj["agent_sdk_version"]) if _is_set(obj.get("agent_sdk_version")) else "",
        is_interactive=bool(obj["is_interactive"]) if _is_set(obj.get("is_interactive")) else False,
        client_type=str(obj["client_type"]) if _is_set(obj.get("client_type")) else "",
        process=str(obj["process"]) if _is_set(obj.get("process")) else "",
        additional_metadata=str(obj["additional_metadata"]) if _is_set(obj.get("additional_metadata")) else "",
        auth=public_api_auth_from_json(auth_raw) if _is_set(auth_raw) else None,
        server_timestamp=parse_flexible_timestamp(st_raw) if _is_set(st_raw) else None,
        event_id=str(obj["event_id"]) if _is_set(obj.get("event_id")) else "",
        device_id=str(obj["device_id"]) if _is_set(obj.get("device_id")) else "",
        swe_bench_run_id=str(obj["swe_bench_run_id"]) if _is_set(obj.get("swe_bench_run_id")) else "",
        swe_bench_instance_id=str(obj["swe_bench_instance_id"]) if _is_set(obj.get("swe_bench_instance_id")) else "",
        swe_bench_task_id=str(obj["swe_bench_task_id"]) if _is_set(obj.get("swe_bench_task_id")) else "",
        email=str(obj["email"]) if _is_set(obj.get("email")) else "",
        agent_id=str(obj["agent_id"]) if _is_set(obj.get("agent_id")) else "",
        parent_session_id=str(obj["parent_session_id"]) if _is_set(obj.get("parent_session_id")) else "",
        agent_type=str(obj["agent_type"]) if _is_set(obj.get("agent_type")) else "",
        slack=slack_context_from_json(slack_raw) if _is_set(slack_raw) else None,
        team_name=str(obj["team_name"]) if _is_set(obj.get("team_name")) else "",
        skill_name=str(obj["skill_name"]) if _is_set(obj.get("skill_name")) else "",
        plugin_name=str(obj["plugin_name"]) if _is_set(obj.get("plugin_name")) else "",
        marketplace_name=str(obj["marketplace_name"]) if _is_set(obj.get("marketplace_name")) else "",
    )


def claude_code_internal_event_to_json(message: ClaudeCodeInternalEvent) -> dict[str, Any]:
    obj: dict[str, Any] = {}
    if message.event_name:
        obj["event_name"] = message.event_name
    if message.client_timestamp is not None:
        obj["client_timestamp"] = datetime_to_iso_z(message.client_timestamp)
    if message.model:
        obj["model"] = message.model
    if message.session_id:
        obj["session_id"] = message.session_id
    if message.user_type:
        obj["user_type"] = message.user_type
    if message.betas:
        obj["betas"] = message.betas
    if message.env is not None:
        obj["env"] = environment_metadata_to_json(message.env)
    if message.entrypoint:
        obj["entrypoint"] = message.entrypoint
    if message.agent_sdk_version:
        obj["agent_sdk_version"] = message.agent_sdk_version
    if message.is_interactive:
        obj["is_interactive"] = message.is_interactive
    if message.client_type:
        obj["client_type"] = message.client_type
    if message.process:
        obj["process"] = message.process
    if message.additional_metadata:
        obj["additional_metadata"] = message.additional_metadata
    if message.auth is not None:
        obj["auth"] = public_api_auth_to_json(message.auth)
    if message.server_timestamp is not None:
        obj["server_timestamp"] = datetime_to_iso_z(message.server_timestamp)
    if message.event_id:
        obj["event_id"] = message.event_id
    if message.device_id:
        obj["device_id"] = message.device_id
    if message.swe_bench_run_id:
        obj["swe_bench_run_id"] = message.swe_bench_run_id
    if message.swe_bench_instance_id:
        obj["swe_bench_instance_id"] = message.swe_bench_instance_id
    if message.swe_bench_task_id:
        obj["swe_bench_task_id"] = message.swe_bench_task_id
    if message.email:
        obj["email"] = message.email
    if message.agent_id:
        obj["agent_id"] = message.agent_id
    if message.parent_session_id:
        obj["parent_session_id"] = message.parent_session_id
    if message.agent_type:
        obj["agent_type"] = message.agent_type
    if message.slack is not None:
        obj["slack"] = slack_context_to_json(message.slack)
    if message.team_name:
        obj["team_name"] = message.team_name
    if message.skill_name:
        obj["skill_name"] = message.skill_name
    if message.plugin_name:
        obj["plugin_name"] = message.plugin_name
    if message.marketplace_name:
        obj["marketplace_name"] = message.marketplace_name
    return obj


def claude_code_internal_event_from_partial(obj: Any) -> ClaudeCodeInternalEvent:
    if not isinstance(obj, dict):
        return ClaudeCodeInternalEvent()
    env_raw = obj.get("env")
    auth_raw = obj.get("auth")
    slack_raw = obj.get("slack")
    ct_raw = obj.get("client_timestamp")
    st_raw = obj.get("server_timestamp")
    return ClaudeCodeInternalEvent(
        event_name=str(obj.get("event_name", "") or ""),
        client_timestamp=parse_flexible_timestamp(ct_raw) if ct_raw is not None else None,
        model=str(obj.get("model", "") or ""),
        session_id=str(obj.get("session_id", "") or ""),
        user_type=str(obj.get("user_type", "") or ""),
        betas=str(obj.get("betas", "") or ""),
        env=environment_metadata_from_partial(env_raw) if isinstance(env_raw, dict) else None,
        entrypoint=str(obj.get("entrypoint", "") or ""),
        agent_sdk_version=str(obj.get("agent_sdk_version", "") or ""),
        is_interactive=bool(obj.get("is_interactive", False)),
        client_type=str(obj.get("client_type", "") or ""),
        process=str(obj.get("process", "") or ""),
        additional_metadata=str(obj.get("additional_metadata", "") or ""),
        auth=public_api_auth_from_partial(auth_raw) if isinstance(auth_raw, dict) else None,
        server_timestamp=parse_flexible_timestamp(st_raw) if st_raw is not None else None,
        event_id=str(obj.get("event_id", "") or ""),
        device_id=str(obj.get("device_id", "") or ""),
        swe_bench_run_id=str(obj.get("swe_bench_run_id", "") or ""),
        swe_bench_instance_id=str(obj.get("swe_bench_instance_id", "") or ""),
        swe_bench_task_id=str(obj.get("swe_bench_task_id", "") or ""),
        email=str(obj.get("email", "") or ""),
        agent_id=str(obj.get("agent_id", "") or ""),
        parent_session_id=str(obj.get("parent_session_id", "") or ""),
        agent_type=str(obj.get("agent_type", "") or ""),
        slack=slack_context_from_partial(slack_raw) if isinstance(slack_raw, dict) else None,
        team_name=str(obj.get("team_name", "") or ""),
        skill_name=str(obj.get("skill_name", "") or ""),
        plugin_name=str(obj.get("plugin_name", "") or ""),
        marketplace_name=str(obj.get("marketplace_name", "") or ""),
    )
