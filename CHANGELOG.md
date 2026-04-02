# Changelog

All notable changes to the **claude-code** Python migration (`claude-code` on PyPI, import name `claude_code`) are documented in this file.

The format is inspired by [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), with extra sections for migration context.

---

## [0.1.0] — 2026-04-02

### Summary

Initial public alpha of the **TypeScript → Python** migration: a single installable package with Typer CLI, dual query-engine layers, a lazy-loaded built-in tool registry, httpx/Anthropic API services, MCP integration types and clients, and broad parity-oriented modules under `src/claude_code/`.

**Distribution:** `claude-code` **0.1.0** · **Python ≥ 3.11** · **License:** MIT (per `pyproject.toml`)

---

### Added — Installable package

- **Single wheel package** `claude_code` built from `src/claude_code` (Hatchling); console script **`claude`** → `claude_code.cli.main:main`.
- **Runtime dependencies:** `anthropic`, `mcp`, `pydantic`, `httpx`, `httpx-sse`, `aiofiles`, `anyio`, `typer`, `rich`, `tiktoken`, `python-dotenv`, `structlog`, `pyyaml`, `websockets`, `json5`, `Pillow`, `packaging`, `pyautogui`.
- **Optional extras:** `dev` (pytest, pytest-asyncio, pytest-cov, mypy, ruff), `telemetry` (OpenTelemetry API/SDK/OTLP HTTP).

---

### Added — Migrated application packages (high level)

These **subpackages** mirror the upstream Claude Code architecture (many files carry `Migrated from: …` notes):

| Area | Package / module (examples) |
|------|-----------------------------|
| **Analytics & assistant** | `analytics`, `assistant` |
| **Auth & bootstrap** | `auth`, `bootstrap` |
| **Bridge & host** | `bridge`, `server` |
| **CLI & entry** | `cli`, `entrypoints` |
| **Commands** | `commands` (slash commands, registry) |
| **Config & constants** | `config`, `constants` |
| **Core engine (alternate stack)** | `core` (tool registry, `core.query_engine`, Anthropic helpers) |
| **Cost** | `cost` |
| **Primary engine (CLI/SDK shape)** | `engine` (`QueryEngine`, `QueryEngineConfig`, `ask`) |
| **Events & history** | `event_handlers`, `history` |
| **Hooks & keybindings** | `hooks`, `keybindings` |
| **MCP config types** | `mcp` |
| **Memory** | `memdir`, `memory` |
| **Migrations** | `migrations` |
| **Model** | `model` |
| **Native** | `native` |
| **Permissions** | `permissions` |
| **Plugins** | `plugins` |
| **Prompts & query helpers** | `prompts`, `query` |
| **Remote** | `remote` |
| **Schemas** | `schemas` |
| **Services** | `services` (see below) |
| **Session & state** | `session`, `state` |
| **Skills & tasks** | `skills`, `tasks` |
| **Tools** | `tools` (see below) |
| **Types** | `types` (messages, permissions, logs, plugins, generated events, …) |
| **Upstream proxy** | `upstreamproxy` |
| **Utilities** | `utils` (env, git, file, shell, permissions, telemetry, plugins, computer_use, …) |
| **Vim & voice** | `vim`, `voice` |

**Top-level modules** (alongside packages): `context`, `inbound_message_context`, `input_history`, `project_onboarding_state`, `query_runner`, `session_setup_runner`, `setup`, `tasks_registry`, `tools_assembly`, `cost_summary_hook`, and related glue.

---

### Added — Migrated services (`claude_code.services`)

Subpackages and modules providing **network clients**, **product-oriented behavior**, and **background capabilities** (names aligned with TS `services/*`):

| Service / submodule | Role |
|---------------------|------|
| **`api`** | Anthropic HTTP client, streaming, retries, bootstrap, utilization, logging, Grove/subscription helpers, and related endpoints |
| **`mcp`** | MCP runtime (stdio/SSE/HTTP/WebSocket-oriented client flows, registry, orchestration) |
| **`oauth`** | OAuth PKCE (`OAuthService`, verifiers/challenges/state) |
| **`compact`** | Context / session compaction |
| **`session_memory`**, **`extract_memories`**, **`team_memory_sync`** | Memory extraction, persistence, team sync |
| **`lsp`** | Language Server Protocol client |
| **`bedrock`**, **`claude_ai`**, **`auth`** | Provider-specific and Claude.ai paths |
| **`docker`** | Docker / environment helpers |
| **`analytics`**, **`notifier`** | Analytics hooks, desktop/terminal notifications |
| **`plugins`**, **`settings_sync`**, **`remote_managed_settings`** | Plugins, settings sync, remote-managed settings |
| **`prompt_suggestion`**, **`auto_dream`**, **`magic_docs`**, **`tips`** | Prompt suggestions, speculation flags, docs/tips |
| **`policy_limits`**, **`rate_limit`**, **`limits`** | Org/policy limits, rate-limit messaging and client state |
| **`diagnostics`** | Diagnostic tracking |
| **`agent_summary`**, **`tool_use_summary`** | Run summaries |
| **`tools`** (under services) | Tool-use orchestration (e.g. concurrency limits) |

**Standalone service modules:** `away_summary`, `internal_logging`, `prevent_sleep`, `vcr`, `voice`, `voice_keyterms`, `voice_stream_stt`, `token_estimation`, `rate_limit_messages`, etc.

---

### Added — Migrated tools (`claude_code.tools`)

- **~88 feature directories** under `src/claude_code/tools/` (count includes `shared/` and grouped packages; exact count may drift—prefer `find src/claude_code/tools -maxdepth 1 -type d` for current total).
- **Registry** (`claude_code.core.tools_registry`): lazy imports, environment-gated sets (simple mode, REPL, coordinator, embedded search, todo v2, tool search), deny-rule filtering, MCP deduplication (**built-ins win** over MCP name collisions).
- **Base layers:** `claude_code.tools.base` (Pydantic `Tool` / `execute` pattern) and `claude_code.core.tool` (registry / Anthropic-oriented ABC)—**both exist** for migration parity; new tools should follow existing neighbors.

**Built-ins loaded by `get_all_base_tools` / `_get_all_base_tools_impl` (order, subject to `ImportError` and env flags):**

| # | Implementation anchor | Model-facing name (typical) |
|---|------------------------|----------------------------|
| 1 | `AgentTool` | `Task` |
| 2 | `TaskOutputTool` | (task output) |
| 3 | `BashTool` | `Shell` |
| 4–5 | `GlobTool`, `GrepTool` | `Glob`, `Grep` — omitted if `CLAUDE_CODE_EMBEDDED_SEARCH` |
| 6 | `FileReadTool` | `Read` |
| 7 | `FileEditTool` | `StrReplace` |
| 8 | `FileWriteTool` | `Write` |
| 9 | `NotebookEditTool` | `NotebookEdit` |
| 10 | `WebFetchTool` | `WebFetch` |
| 11 | `WebSearchTool` | `WebSearch` |
| 12 | `TodoWriteTool` | `TodoWrite` |
| 13 | `AskUserQuestionTool` | (ask user) |
| 14 | `SkillTool` | `Skill` |
| 15 | `BriefTool` | `Brief` |
| — | `TaskCreate`, `TaskGet`, `TaskUpdate`, `TaskList` | When `CLAUDE_CODE_TODO_V2` |
| — | `ListMcpResourcesTool`, `ReadMcpResourceTool` | MCP resources |
| — | `ToolSearchTool` | When `CLAUDE_CODE_TOOL_SEARCH` |

**Additional tool packages** exist under `tools/` for parity, tests, or alternate code paths (e.g. `mcp_tool`, `config_tool`, `lsp_tool`, `plan_mode`, `worktree`, `powershell_tool`, `image_tool`, `repl`, `schedule_cron`, `team_create`, …)—not every module is wired into `_get_all_base_tools_impl`. See `docs/TOOLS.md`.

**Environment flags** (selection): `CLAUDE_CODE_SIMPLE`, `CLAUDE_CODE_REPL_MODE`, `CLAUDE_CODE_TODO_V2`, `CLAUDE_CODE_TOOL_SEARCH`, `CLAUDE_CODE_EMBEDDED_SEARCH`, `CLAUDE_CODE_COORDINATOR_MODE`, `CLAUDE_CODE_WORKTREE_MODE`, `CLAUDE_CODE_AGENT_SWARMS`, file-read and tool-concurrency limits per docs.

---

### Added — CLI implementation

- **Framework:** Typer application `claude_code.cli.main:app`.
- **Default invocation:** callback runs **interactive chat** or **print mode** when `--print` / `--prompt` is set.
- **Commands:** `chat`, `config` (show path/summary or `--edit`), `doctor` (Python version, API key, config path, git, minimal `QueryEngine` construct), `version`.
- **Common options:** `--version` / `-V`, `--verbose`, `--model` / `-m`, `--print`, `--prompt` / `-p`.
- **Logging:** `structlog` + stdlib logging, stderr-oriented.
- **Session:** integrates `bootstrap.state` (`set_client_type`, `set_is_interactive`, `get_session_id`).

---

### Added — Tests & quality

- **Test layout:** `tests/` with `pytest`, `asyncio_mode = auto`, `pythonpath` including `src` (see `pyproject.toml`).
- **Markers:** `integration` for filesystem/git/subprocess-heavy tests (`pytest -m "not integration"` to skip).
- **Coverage:** `pytest --cov=claude_code --cov-report=term-missing` supported via dev extra.
- **Lint / format:** Ruff (check + format), line length 120, Python 3.11 target.
- **Typing:** mypy configured with **gradual** project-wide settings (`strict = false` in `pyproject.toml` with planned tightening); `contributing.md` recommends `mypy src` before PRs.

**Project-reported baseline (README badge, refresh locally):** on order of **330+ tests passing**, **2 skipped**—exact counts change with commits; always run `pytest` on **Python 3.11+**.

---

## Migration highlights

### Converted from TypeScript

- **Agentic loop & messaging:** Messages API usage, tool-use execution, streaming patterns, session and permission contexts—ported to **asyncio** with **`anthropic`**, **`httpx`**, and **Pydantic** models.
- **Tool surface:** Filesystem, shell, search, web, notebook, tasks/agents, MCP resource tools, and registry policy presets from TS tool and permissions concepts.
- **Services layer:** API client, retries, OAuth, compaction, LSP, MCP clients, limits, notifications, plugins/sync, analytics, Bedrock-related paths—**parity-oriented module names**.
- **Infrastructure:** Constants, config (`config.json` semantics), hooks, commands registry, bridge/remote/session types, skills/memdir, migrations, large `utils/` tree (git, env, shell, plugins, telemetry).
- **Types:** Message and permission types, logs, hooks, generated event payloads under `types/generated/`.
- **CLI:** Behavioral subset of the TS CLI (doctor, config, version, chat/print); **not** a full Ink UI port.

### Intentionally not migrated (or only partially)

- **Ink / React TUI:** The interactive terminal UI from the reference product is **not** ported. Python CLI is **stdin/stdout**-oriented; **Rich** is a dependency but does not replicate the full TUI.
- **React hooks:** TS `use*` hooks are **not** translated 1:1; behavior is approximated with asyncio, services, and `event_handlers` where needed. See `MIGRATION_STATUS.md` for remaining hook-shaped gaps.
- **Computer use:** **Partial**—`pyautogui` and `utils/computer_use/` exist; full product parity (MCP host, adapters, drain loops) is incomplete.
- **Telemetry:** **structlog** baseline; **OpenTelemetry** behind `[telemetry]` extra; Perfetto/BigQuery-style exporters from TS are not fully replicated.
- **MCP host entrypoint:** `entrypoints.start_mcp_server` described in docs as **stub** until handlers are fully ported.

### Architecture decisions

1. **Dual `QueryEngine` stacks:**  
   - **`claude_code.engine`:** High-level, SDK-shaped API used by CLI and `ask()`; documented as primary for package ergonomics.  
   - **`claude_code.core.query_engine`:** Lower-level loop with **Anthropic Messages + tool execution**.  
   **Implication:** Integrators needing a **working multi-turn tool loop today** should follow **`core.query_engine`** patterns (e.g. integration tests); CLI wiring may still use **`engine`** with a **simplified / placeholder** inner loop—see `README.md` “Choosing a QueryEngine”.

2. **Dual tool base types:** `tools.base.Tool` (Pydantic tools) vs `core.tool.Tool` (registry ABC)—preserved to reduce friction during the port; registry lazy-imports concrete tools.

3. **Single package, not a monorepo:** All product code ships as one **`claude_code`** namespace for simpler installs and imports.

4. **Parity over purity:** CamelCase fields, legacy tool name aliases in policy sets (`Bash`/`Edit` vs `Shell`/`StrReplace`), and ruff/mypy ignores document TS mirroring.

5. **Feature flags:** Environment variables preserve upstream modes (simple, REPL, coordinator, embedded search, todo v2, tool search).

---

## Known issues and limitations

### Functional

- **CLI `QueryEngine` default:** `_create_cli_query_engine` passes **`tools=[]`**—minimal smoke/doctor alignment; not the full default tool pool of the reference product until wired to `assemble_tool_pool` / registry.
- **Engine vs core loop:** Until consolidated, documentation and behavior can diverge between **`engine.QueryEngine`** and **`core.query_engine.QueryEngine`**.
- **MCP server host:** Full MCP **host** parity may be incomplete (stub entrypoints per README/docs).
- **Optional / alternate tools:** Many modules under `tools/` are not registered in `_get_all_base_tools_impl`; some are for future parity or alternate entry paths.

### Platform & environment

- **Python 3.11+ required** (`| None` syntax and project metadata); older interpreters fail at import/collection time.
- **External binaries:** `Glob`/`Grep` tooling may expect **ripgrep** or similar on PATH depending on implementation paths.
- **OS-specific behavior:** Notifications, sandbox, computer-use, and shell providers may behave differently than macOS-centric upstream assumptions.

### Quality & maintenance

- **mypy:** Project uses **gradual** typing globally (`strict = false` in `pyproject.toml`); strictness is tightened in spirit via `check_untyped_defs` and overrides—expect ongoing type work.
- **Test counts:** README badges and `MIGRATION_STATUS.md` totals can **drift**; treat **`pytest`** on 3.11+ as source of truth.
- **Community fork:** This repository is a **community migration**; it is **not** an official Anthropic product release. Trade names refer to interoperability targets.

### Security & operations

- **Secrets:** Use **`ANTHROPIC_API_KEY`** and environment-based config; never commit credentials.
- **Permissions:** Tool execution and MCP tools remain **high risk**; run in trusted environments with deny rules and sandboxing as appropriate.

---

## References

- `README.md` — install, CLI, engine choice, comparison table  
- `docs/ARCHITECTURE.md`, `docs/PACKAGES.md`, `docs/TOOLS.md`, `docs/SERVICES.md`, `docs/API.md`, `docs/DATA_FLOW.md`  
- `MIGRATION_STATUS.md` — phased backlog (hooks, computer use, shell providers, telemetry, optional UI)  
- `MIGRATION_PLAN/` (repository root) — indexed migration plan markdown  

---

*Changelog maintained for the Python migration workspace. Update this file when releasing new versions or closing major migration gaps.*
