# Python API reference

Public and semi-public APIs for integrating **claude-code-python** as a library. This is not the Anthropic REST API — it documents **this repository’s** Python modules.

## Package entry

```python
import claude_code

claude_code.__version__  # "0.1.0"
```

Re-exported symbols include `QueryEngine`, `QueryEngineConfig`, `Tool`, `ToolResult`, message types, `get_session_id`, `Command`, `get_command`, and hook helpers — see `claude_code.__all__`.

## Engine: `QueryEngine` and `QueryEngineConfig`

**Module:** `claude_code.engine.query_engine`

### `QueryEngineConfig` (dataclass)

Primary fields used by integrators:

| Field | Type | Description |
|-------|------|-------------|
| `cwd` | `str` | Working directory for the session. |
| `tools` | `Tools` | List of tool instances (see note below). |
| `commands` | `list[Command]` | Slash commands available to the engine. |
| `mcp_clients` | `list[Any]` | MCP client handles. |
| `agents` | `list[AgentDefinition]` | Agent definitions. |
| `can_use_tool` | `Callable` | Permission gate: must return a dict including `{"allowed": bool, ...}`. |
| `get_app_state` | `Callable[[], AppState]` | Read mutable app state. |
| `set_app_state` | `Callable[[Callable[[AppState], AppState]], None]` | Update app state. |
| `initial_messages` | `list[Message] \| None` | Seed conversation. |
| `read_file_cache` | `FileStateCache \| None` | File read dedupe cache. |
| `custom_system_prompt` / `append_system_prompt` | `str \| None` | Prompt overrides. |
| `user_specified_model` / `fallback_model` | `str \| None` | Model selection. |
| `thinking_config` | `ThinkingConfig \| None` | Extended thinking mode. |
| `max_turns` / `max_budget_usd` / `task_budget` | limits | Safety / cost caps. |
| `json_schema` | `dict \| None` | Structured output schema when supported. |
| `verbose` | `bool` | Verbose logging. |
| `handle_elicitation` | `Callable \| None` | Elicitation UI hook. |
| `abort_controller` | `Any \| None` | Cooperative cancel. |
| `orphaned_permission` | `OrphanedPermission \| None` | Resume permission state. |

`Tools` in type hints refers to `claude_code.core.tool.Tools` (`list[Tool]`) under `TYPE_CHECKING` — pass the tool list your stack expects (registry outputs or custom adapters).

### `QueryEngine` methods

| Method | Description |
|--------|-------------|
| `async submit_message(prompt, options=None)` | `AsyncIterator[SDKMessage]` — streams progress; ends with `SDKResultMessage`. |
| `get_messages()` | Current `list[Message]`. |
| `get_read_file_state()` | `FileStateCache`. |
| `get_session_id()` | Delegates to `bootstrap.state.get_session_id`. |
| `set_model(model: str)` | Sets `config.user_specified_model`. |

### `ask()` — one-shot helper

```python
async def ask(
    *,
    commands: list[Command],
    prompt: str | list[dict[str, Any]],
    prompt_uuid: str | None = None,
    is_meta: bool = False,
    cwd: str,
    tools: Tools,
    mcp_clients: list[Any] | None = None,
    verbose: bool = False,
    thinking_config: ThinkingConfig | None = None,
    max_turns: int | None = None,
    max_budget_usd: float | None = None,
    task_budget: dict[str, int] | None = None,
    can_use_tool: Callable[..., Any],
    mutable_messages: list[Message] | None = None,
    get_read_file_cache: Callable[[], FileStateCache] | None = None,
    set_read_file_cache: Callable[[FileStateCache], None] | None = None,
    custom_system_prompt: str | None = None,
    append_system_prompt: str | None = None,
    user_specified_model: str | None = None,
    fallback_model: str | None = None,
    json_schema: dict[str, Any] | None = None,
    get_app_state: Callable[[], AppState],
    set_app_state: Callable[[Callable[[AppState], AppState]], None],
    abort_controller: Any | None = None,
    replay_user_messages: bool = False,
    include_partial_messages: bool = False,
    handle_elicitation: Callable[..., Any] | None = None,
    agents: list[AgentDefinition] | None = None,
    set_sdk_status: Callable[[Any], None] | None = None,
    orphaned_permission: OrphanedPermission | None = None,
) -> AsyncIterator[SDKMessage]:
```

Builds a `QueryEngine` with `QueryEngineConfig`, runs `submit_message`, and optionally writes back the read-file cache.

### SDK message types (engine)

- `SDKMessage` — base with `type`, `session_id`, `uuid`.
- `SDKResultMessage` — final summary: `result`, `usage`, `total_cost_usd`, `permission_denials`, `structured_output`, `errors`, etc.
- `SDKPermissionDenial` — `tool_name`, `tool_use_id`, `tool_input`.

## CLI construction example

From `cli/main.py`, a minimal engine for local experimentation:

```python
from claude_code.engine.query_engine import QueryEngine, QueryEngineConfig, AppState
from claude_code.core.tool import get_empty_tool_permission_context

app_state_holder = [AppState(tool_permission_context=get_empty_tool_permission_context())]

def get_app_state():
    return app_state_holder[0]

def set_app_state(updater):
    app_state_holder[0] = updater(app_state_holder[0])

def can_use_tool(_tool_name: str, _tool_input: dict) -> dict:
    return {"allowed": True}

config = QueryEngineConfig(
    cwd="/path/to/project",
    tools=[],
    commands=[],
    mcp_clients=[],
    agents=[],
    can_use_tool=can_use_tool,
    get_app_state=get_app_state,
    set_app_state=set_app_state,
    user_specified_model=None,
    verbose=False,
)
engine = QueryEngine(config)
```

Populate `tools` via `assemble_tool_pool` from `claude_code.core.tools_registry` for real agent behavior.

## Tools API (`claude_code.tools.base`)

```python
from claude_code.tools.base import Tool, ToolResult, ToolUseContext

class MyTool(Tool[MyInput, MyOutput]):
    @property
    def name(self) -> str: ...
    def get_input_schema(self) -> dict: ...
    async def execute(self, input_data: MyInput, context: ToolUseContext) -> ToolResult: ...
```

## Hooks API

```python
from claude_code.hooks import register_hook, execute_hooks, HookEvent, HookResult
```

Use for lifecycle or permission-related extensions.

## Config API

```python
from claude_code.config import get_global_config, set_global_config, get_project_config, get_config_path
```

- `get_config_path()` → path to `config.json`.
- `GlobalConfig` / `ProjectConfig` dataclasses in `claude_code.config.types`.

## MCP types API

```python
from claude_code.mcp import McpStdioServerConfig, McpSSEServerConfig, McpHTTPServerConfig
```

Use for describing servers; runtime connection lives under `services.mcp`.

## SDK types (`entrypoints.sdk_types`)

`SDKConfig`, `SDKMessage`, `SDKContentBlock`, `SDKUsage` — higher-level SDK-shaped types for integrations (parallel to engine messages).

## Core alternate `QueryEngine`

`claude_code.core.query_engine` exposes another `QueryEngine` / `QueryEngineConfig` tied to `AsyncAnthropic` and `core.tool` — use when extending low-level tool execution; prefer `claude_code.engine` for normal imports.

## Configuration reference (environment)

| Variable | Used by |
|----------|---------|
| `ANTHROPIC_API_KEY`, `ANTHROPIC_BASE_URL`, `ANTHROPIC_MODEL` | `services.api` defaults |
| `CLAUDE_CODE_MODEL` | Engine default model |
| `CLAUDE_CODE_THINKING` | Default thinking mode |
| `CLAUDE_CONFIG_DIR` | Config dir / session storage |
| `CLAUDE_CODE_SESSION_ID` | Session id (set in init if missing) |

See [ARCHITECTURE.md](./ARCHITECTURE.md) and [TOOLS.md](./TOOLS.md) for tool-related env vars.

## Command-line

After install:

```bash
claude --help
claude --version
```

Entry: `claude_code.cli.main:main` (Typer).

## Related documents

- [ARCHITECTURE.md](./ARCHITECTURE.md)
- [PACKAGES.md](./PACKAGES.md)
- [DATA_FLOW.md](./DATA_FLOW.md)
- [TOOLS.md](./TOOLS.md)
- [SERVICES.md](./SERVICES.md)
