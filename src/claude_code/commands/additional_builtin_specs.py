"""
CommandSpec entries for built-ins that were implemented as Command classes only.

Migrated from the corresponding ``commands/*/index.ts`` and top-level ``commands/*.ts``
files; kept here to avoid circular imports and to complete ``built_in_command_specs()``.
"""

from __future__ import annotations

import os

from claude_code.auth.helpers import get_subscription_type
from claude_code.commands._immediate import should_inference_config_command_be_immediate
from claude_code.commands.init_project.command import init_description
from claude_code.commands.install_github_app.command import is_install_github_app_enabled
from claude_code.commands.login.command import login_description, login_is_enabled
from claude_code.commands.remote.env_command import remote_env_is_enabled, remote_env_is_hidden
from claude_code.commands.remote.setup_command import web_setup_is_enabled, web_setup_is_hidden
from claude_code.commands.review.ultrareview_enabled import is_ultrareview_enabled
from claude_code.commands.sandbox.command import sandbox_description, sandbox_hidden
from claude_code.commands.spec import CommandSpec
from claude_code.commands.terminal.command import (
    terminal_setup_description,
    terminal_setup_hidden,
)
from claude_code.commands.voice.command import voice_is_enabled as voice_growthbook_enabled_fn
from claude_code.commands.voice.command import voice_is_hidden as voice_mode_hidden_fn
from claude_code.keybindings import is_keybinding_customization_enabled
from claude_code.utils.auth import has_anthropic_api_key_auth
from claude_code.utils.model.model import get_main_loop_model

CCR_TERMS_URL = "https://code.claude.com/docs/en/claude-code-on-the-web"


def _env_flag_disabled(name: str) -> bool:
    v = os.environ.get(name)
    return v is not None and v.strip().lower() in ("1", "true", "yes", "on")


def _logout_enabled() -> bool:
    return not _env_flag_disabled("DISABLE_LOGOUT_COMMAND")


def _upgrade_enabled() -> bool:
    if _env_flag_disabled("DISABLE_UPGRADE_COMMAND"):
        return False
    return get_subscription_type() != "enterprise"


def _passes_description() -> str:
    from claude_code.services.api.referral import get_cached_referrer_reward

    # org_id unknown at static registration; reward text mirrors TS when no org.
    if get_cached_referrer_reward(None) is not None:
        return "Share a free week of Claude Code with friends and earn extra usage"
    return "Share a free week of Claude Code with friends"


def _passes_hidden() -> bool:
    from claude_code.services.api.referral import check_cached_passes_eligibility

    st = check_cached_passes_eligibility(None)
    return not st["eligible"] or not st["has_cache"]


def _model_description() -> str:
    return f"Set the AI model for Claude Code (currently {get_main_loop_model()})"


def _login_description() -> str:
    return login_description(has_anthropic_api_key_auth())


def _remote_env_enabled() -> bool:
    return remote_env_is_enabled(
        is_claude_ai_subscriber=True,
        allow_remote_sessions=True,
    )


def _remote_env_hidden() -> bool:
    return remote_env_is_hidden(
        is_claude_ai_subscriber=True,
        allow_remote_sessions=True,
    )


def _web_setup_enabled() -> bool:
    return web_setup_is_enabled(
        feature_cobalt_lantern=True,
        allow_remote_sessions=True,
    )


def _web_setup_hidden() -> bool:
    return web_setup_is_hidden(allow_remote_sessions=True)


def _terminal_hidden() -> bool:
    return terminal_setup_hidden()


def _voice_growthbook_enabled() -> bool:
    return voice_growthbook_enabled_fn(
        growthbook_voice=os.environ.get("CLAUDE_CODE_VOICE_GROWTHBOOK", "").lower() in ("1", "true", "yes", "on"),
    )


def _voice_mode_hidden() -> bool:
    return voice_mode_hidden_fn(
        voice_mode_enabled=os.environ.get("CLAUDE_CODE_VOICE_MODE", "").lower() in ("1", "true", "yes", "on"),
    )


HOOKS_COMMAND_SPEC = CommandSpec(
    type="local-jsx",
    name="hooks",
    description="View hook configurations for tool events",
    immediate=True,
    load_symbol="claude_code.commands.hooks.command",
)

IDE_COMMAND_SPEC = CommandSpec(
    type="local-jsx",
    name="ide",
    description="Manage IDE integrations and show status",
    argument_hint="[open]",
    load_symbol="claude_code.commands.ide.command",
)

INIT_COMMAND_SPEC = CommandSpec(
    type="prompt",
    name="init",
    description="",
    description_fn=init_description,
    content_length=0,
    progress_message="analyzing your codebase",
    source="builtin",
    load_symbol="claude_code.commands.init_project.command",
)

INSIGHTS_COMMAND_SPEC = CommandSpec(
    type="prompt",
    name="insights",
    description="Generate a report analyzing your Claude Code sessions",
    content_length=0,
    progress_message="analyzing your sessions",
    source="builtin",
    load_symbol="claude_code.commands.insights.command",
)

INSTALL_GITHUB_APP_COMMAND_SPEC = CommandSpec(
    type="local-jsx",
    name="install-github-app",
    description="Set up Claude GitHub Actions for a repository",
    availability=("claude-ai", "console"),
    is_enabled=is_install_github_app_enabled,
    load_symbol="claude_code.commands.install_github_app.command",
)

INSTALL_SLACK_APP_COMMAND_SPEC = CommandSpec(
    type="local",
    name="install-slack-app",
    description="Install the Claude Slack app",
    availability=("claude-ai",),
    supports_non_interactive=False,
    load_symbol="claude_code.commands.install_slack_app.install_slack_app",
)

KEYBINDINGS_COMMAND_SPEC = CommandSpec(
    type="local",
    name="keybindings",
    description="Open or create your keybindings configuration file",
    supports_non_interactive=False,
    is_enabled=is_keybinding_customization_enabled,
    load_symbol="claude_code.commands.keybindings.keybindings",
)

LOGIN_COMMAND_SPEC = CommandSpec(
    type="local-jsx",
    name="login",
    description="",
    description_fn=_login_description,
    is_enabled=login_is_enabled,
    load_symbol="claude_code.commands.login.command",
)

LOGOUT_COMMAND_SPEC = CommandSpec(
    type="local-jsx",
    name="logout",
    description="Sign out from your Anthropic account",
    is_enabled=_logout_enabled,
    load_symbol="claude_code.commands.logout.command",
)

MCP_COMMAND_SPEC = CommandSpec(
    type="local-jsx",
    name="mcp",
    description="Manage MCP servers",
    immediate=True,
    argument_hint="[enable|disable [server-name]]",
    load_symbol="claude_code.commands.mcp.command",
)

MEMORY_COMMAND_SPEC = CommandSpec(
    type="local-jsx",
    name="memory",
    description="Edit Claude memory files",
    load_symbol="claude_code.commands.memory.command",
)

MODEL_COMMAND_SPEC = CommandSpec(
    type="local-jsx",
    name="model",
    description="",
    description_fn=_model_description,
    argument_hint="[model]",
    immediate_fn=should_inference_config_command_be_immediate,
    load_symbol="claude_code.commands.model.command",
)

OUTPUT_STYLE_COMMAND_SPEC = CommandSpec(
    type="local-jsx",
    name="output-style",
    description="Deprecated: use /config to change output style",
    hidden=True,
    load_symbol="claude_code.commands.output_style.command",
)

REMOTE_ENV_COMMAND_SPEC = CommandSpec(
    type="local-jsx",
    name="remote-env",
    description="Configure the default remote environment for teleport sessions",
    is_enabled=_remote_env_enabled,
    is_hidden_fn=_remote_env_hidden,
    load_symbol="claude_code.commands.remote.env_command",
)

PLUGIN_COMMAND_SPEC = CommandSpec(
    type="local-jsx",
    name="plugin",
    description="Manage Claude Code plugins",
    aliases=("plugins", "marketplace"),
    immediate=True,
    load_symbol="claude_code.commands.plugins.command",
)

PR_COMMENTS_COMMAND_SPEC = CommandSpec(
    type="prompt",
    name="pr-comments",
    description="Get comments from a GitHub pull request",
    content_length=0,
    progress_message="fetching PR comments",
    source="builtin",
    load_symbol="claude_code.commands.pr_comments.command",
)

PASSES_COMMAND_SPEC = CommandSpec(
    type="local-jsx",
    name="passes",
    description="",
    description_fn=_passes_description,
    is_hidden_fn=_passes_hidden,
    load_symbol="claude_code.commands.passes.command",
)

PERMISSIONS_COMMAND_SPEC = CommandSpec(
    type="local-jsx",
    name="permissions",
    description="Manage allow & deny tool permission rules",
    aliases=("allowed-tools",),
    load_symbol="claude_code.commands.permissions.command",
)

PLAN_COMMAND_SPEC = CommandSpec(
    type="local-jsx",
    name="plan",
    description="Enable plan mode or view the current session plan",
    argument_hint="[open|<description>]",
    load_symbol="claude_code.commands.plan.command",
)

RESUME_COMMAND_SPEC = CommandSpec(
    type="local-jsx",
    name="resume",
    description="Resume a previous conversation",
    aliases=("continue",),
    argument_hint="[conversation id or search term]",
    load_symbol="claude_code.commands.resume.command",
)

REVIEW_COMMAND_SPEC = CommandSpec(
    type="prompt",
    name="review",
    description="Review a pull request",
    content_length=0,
    progress_message="reviewing pull request",
    source="builtin",
    load_symbol="claude_code.commands.review.command",
)

ULTRAREVIEW_COMMAND_SPEC = CommandSpec(
    type="local-jsx",
    name="ultrareview",
    description=(
        f"~10–20 min · Finds and verifies bugs in your branch. Runs in Claude Code on the web. See {CCR_TERMS_URL}"
    ),
    is_enabled=is_ultrareview_enabled,
    load_symbol="claude_code.commands.review.command",
)

UPGRADE_COMMAND_SPEC = CommandSpec(
    type="local-jsx",
    name="upgrade",
    description="Upgrade to Max for higher rate limits and more Opus",
    availability=("claude-ai",),
    is_enabled=_upgrade_enabled,
    load_symbol="claude_code.commands.upgrade.command",
)

VIM_COMMAND_SPEC = CommandSpec(
    type="local",
    name="vim",
    description="Toggle between Vim and Normal editing modes",
    supports_non_interactive=False,
    load_symbol="claude_code.commands.vim.vim_call",
)

VOICE_COMMAND_SPEC = CommandSpec(
    type="local",
    name="voice",
    description="Toggle voice mode",
    availability=("claude-ai",),
    supports_non_interactive=False,
    is_enabled=_voice_growthbook_enabled,
    is_hidden_fn=_voice_mode_hidden,
    load_symbol="claude_code.commands.voice.voice_call",
)

SANDBOX_COMMAND_SPEC = CommandSpec(
    type="local-jsx",
    name="sandbox",
    description="",
    description_fn=sandbox_description,
    argument_hint='exclude "command pattern"',
    immediate=True,
    is_hidden_fn=sandbox_hidden,
    load_symbol="claude_code.commands.sandbox.command",
)

TERMINAL_SETUP_COMMAND_SPEC = CommandSpec(
    type="local-jsx",
    name="terminal-setup",
    description="",
    description_fn=terminal_setup_description,
    is_hidden_fn=_terminal_hidden,
    load_symbol="claude_code.commands.terminal.command",
)

STATUS_COMMAND_SPEC = CommandSpec(
    type="local-jsx",
    name="status",
    description=("Show Claude Code status including version, model, account, API connectivity, and tool statuses"),
    immediate=True,
    load_symbol="claude_code.commands.status.command",
)

WEB_SETUP_COMMAND_SPEC = CommandSpec(
    type="local-jsx",
    name="web-setup",
    description=("Setup Claude Code on the web (requires connecting your GitHub account)"),
    availability=("claude-ai",),
    is_enabled=_web_setup_enabled,
    is_hidden_fn=_web_setup_hidden,
    load_symbol="claude_code.commands.remote.setup_command",
)

ADDITIONAL_BUILTIN_COMMAND_SPECS: tuple[CommandSpec, ...] = (
    HOOKS_COMMAND_SPEC,
    IDE_COMMAND_SPEC,
    INIT_COMMAND_SPEC,
    INSIGHTS_COMMAND_SPEC,
    INSTALL_GITHUB_APP_COMMAND_SPEC,
    INSTALL_SLACK_APP_COMMAND_SPEC,
    KEYBINDINGS_COMMAND_SPEC,
    LOGIN_COMMAND_SPEC,
    LOGOUT_COMMAND_SPEC,
    MCP_COMMAND_SPEC,
    MEMORY_COMMAND_SPEC,
    MODEL_COMMAND_SPEC,
    OUTPUT_STYLE_COMMAND_SPEC,
    REMOTE_ENV_COMMAND_SPEC,
    PLUGIN_COMMAND_SPEC,
    PR_COMMENTS_COMMAND_SPEC,
    PASSES_COMMAND_SPEC,
    PERMISSIONS_COMMAND_SPEC,
    PLAN_COMMAND_SPEC,
    RESUME_COMMAND_SPEC,
    REVIEW_COMMAND_SPEC,
    ULTRAREVIEW_COMMAND_SPEC,
    UPGRADE_COMMAND_SPEC,
    VIM_COMMAND_SPEC,
    VOICE_COMMAND_SPEC,
    SANDBOX_COMMAND_SPEC,
    TERMINAL_SETUP_COMMAND_SPEC,
    STATUS_COMMAND_SPEC,
    WEB_SETUP_COMMAND_SPEC,
)

__all__ = [
    "ADDITIONAL_BUILTIN_COMMAND_SPECS",
    "HOOKS_COMMAND_SPEC",
    "IDE_COMMAND_SPEC",
    "INIT_COMMAND_SPEC",
    "INSIGHTS_COMMAND_SPEC",
    "INSTALL_GITHUB_APP_COMMAND_SPEC",
    "INSTALL_SLACK_APP_COMMAND_SPEC",
    "KEYBINDINGS_COMMAND_SPEC",
    "LOGIN_COMMAND_SPEC",
    "LOGOUT_COMMAND_SPEC",
    "MCP_COMMAND_SPEC",
    "MEMORY_COMMAND_SPEC",
    "MODEL_COMMAND_SPEC",
    "OUTPUT_STYLE_COMMAND_SPEC",
    "REMOTE_ENV_COMMAND_SPEC",
    "PLUGIN_COMMAND_SPEC",
    "PR_COMMENTS_COMMAND_SPEC",
    "PASSES_COMMAND_SPEC",
    "PERMISSIONS_COMMAND_SPEC",
    "PLAN_COMMAND_SPEC",
    "RESUME_COMMAND_SPEC",
    "REVIEW_COMMAND_SPEC",
    "SANDBOX_COMMAND_SPEC",
    "STATUS_COMMAND_SPEC",
    "TERMINAL_SETUP_COMMAND_SPEC",
    "ULTRAREVIEW_COMMAND_SPEC",
    "UPGRADE_COMMAND_SPEC",
    "VIM_COMMAND_SPEC",
    "VOICE_COMMAND_SPEC",
    "WEB_SETUP_COMMAND_SPEC",
]
