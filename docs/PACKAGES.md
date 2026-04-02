# Packages and modules

The installable distribution is a **single package** `claude_code` (wheel built from `src/claude_code`). There is no multi-package monorepo; this file maps **subpackages** and notable **modules**.

## Installable artifact

| Name | Version source | Console script |
|------|----------------|----------------|
| `claude-code` (`claude_code`) | `pyproject.toml` / `claude_code.__version__` | `claude` → `claude_code.cli.main:main` |

## Top-level subpackages

| Subpackage | Role |
|------------|------|
| `claude_code.analytics` | Analytics hooks / instrumentation. |
| `claude_code.assistant` | Assistant-facing helpers. |
| `claude_code.auth` | Authentication helpers. |
| `claude_code.bootstrap` | Session bootstrap, client type, session id (`get_session_id`). |
| `claude_code.bridge` | Bridge integrations (UI / host). |
| `claude_code.buddy` | Buddy / companion flows. |
| `claude_code.cli` | Typer CLI (`main`), exit codes, output helpers, transports. |
| `claude_code.commands` | Slash commands and command registry (`Command`, `get_command`). |
| `claude_code.config` | `GlobalConfig`, `ProjectConfig`, load/save `config.json`. |
| `claude_code.constants` | Shared constants (product, OAuth, files, tools, …). |
| `claude_code.core` | Tool registry, core `Tool` / `ToolUseContext`, cost tracker, context, **alternate** `QueryEngine` stack. |
| `claude_code.cost` | Cost tracking utilities. |
| `claude_code.engine` | **Primary** `QueryEngine`, `QueryEngineConfig`, `ask()`. |
| `claude_code.entrypoints` | `run_cli`, `initialize`, `shutdown`, SDK-oriented entry. |
| `claude_code.event_handlers` | Event handler registration. |
| `claude_code.history` | Conversation / transcript history. |
| `claude_code.hooks` | `register_hook`, `execute_hooks`, hook events/results. |
| `claude_code.keybindings` | Keybinding definitions. |
| `claude_code.mcp` | MCP server **configuration types** (stdio, SSE, HTTP, scopes). |
| `claude_code.memdir` | Memory directory utilities. |
| `claude_code.memory` | Memory subsystem. |
| `claude_code.migrations` | Data migrations. |
| `claude_code.model` | Model-related helpers. |
| `claude_code.native` | Native integrations. |
| `claude_code.permissions` | Permission models / checks. |
| `claude_code.plugins` | Plugin loading and integration. |
| `claude_code.prompts` | System prompt assembly (`get_system_prompt`, …). |
| `claude_code.query` | Query helpers. |
| `claude_code.remote` | Remote control / scheduling hooks. |
| `claude_code.schemas` | JSON/schema artifacts. |
| `claude_code.server` | `DirectConnectSessionManager`, server message types. |
| `claude_code.services` | API client, OAuth, compaction, LSP, MCP services, limits — see [SERVICES.md](./SERVICES.md). |
| `claude_code.session` | Session storage (`CLAUDE_CONFIG_DIR` aware). |
| `claude_code.skills` | Skills loading, bundled skills, policy. |
| `claude_code.state` | Application state containers. |
| `claude_code.tasks` | Task scheduling / registry support. |
| `claude_code.tools` | All built-in tools — see [TOOLS.md](./TOOLS.md). |
| `claude_code.types` | Messages, IDs, permissions, logs, plugins, … |
| `claude_code.upstreamproxy` | API relay/proxy. |
| `claude_code.utils` | Large utility tree: env, git, plugins, shell, permissions, telemetry, … |
| `claude_code.vim` | Vim mode types/helpers. |
| `claude_code.voice` | Voice / STT enablement flags. |

## Top-level modules (files)

These sit beside subpackages and are imported directly:

| Module | Notes |
|--------|--------|
| `claude_code.context` | Context helpers. |
| `claude_code.history` (root `history.py`) | Legacy/history helpers (package `history/` also exists). |
| `claude_code.inbound_message_context` | Inbound message context. |
| `claude_code.input_history` | Input history. |
| `claude_code.project_onboarding_state` | Onboarding state. |
| `claude_code.query_runner` | Query runner glue. |
| `claude_code.session_setup_runner` | Session setup. |
| `claude_code.setup` | Setup / environment probing (`CLAUDE_CODE_SIMPLE`, bubblewrap, …). |
| `claude_code.tasks_registry` | Task registry. |
| `claude_code.tools_assembly` | Tool assembly helpers. |
| `claude_code.cost_summary_hook` | Cost summary hook. |

## `claude_code.tools` layout

Tools are grouped by **feature folders** (e.g. `tools/bash/`, `tools/file_read/`). Many features also have a `*_tool` package (e.g. `bash_tool/`) for migration parity with TypeScript names. Prefer the **non-`*_tool`** paths when reading the “canonical” implementation for a feature, unless your import path already uses the `*_tool` package.

## `claude_code.utils` highlights

| Area | Path (examples) |
|------|-----------------|
| Environment / paths | `utils/env.py`, `utils/env_utils.py`, `utils/xdg.py` |
| Git | `utils/git.py`, `utils/git_log_parser.py` |
| Files | `utils/file.py`, `utils/file_history.py`, `utils/file_persistence/` |
| Plugins / MCPB | `utils/plugins/` |
| Shell / bash specs | `utils/bash/`, `utils/shell/` |
| Permissions | `utils/permissions/` |
| Messages / format | `utils/messages/`, `utils/format.py` |
| Telemetry | `utils/telemetry/` |
| Suggestions | `utils/suggestions/` |
| Computer use | `utils/computer_use/` |

## Public re-exports

`claude_code.__init__` re-exports:

`QueryEngine`, `QueryEngineConfig`, `Tool`, `ToolResult`, `Message`, `UserMessage`, `AssistantMessage`, `SessionId`, `AgentId`, `get_session_id`, `Command`, `get_command`, hook helpers, and submodules listed in `__all__`.

For programmatic use, prefer:

```python
from claude_code import QueryEngine, QueryEngineConfig
from claude_code.engine import ask
```

See [API.md](./API.md) for signatures and examples.
