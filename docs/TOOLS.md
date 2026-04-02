# Tools reference

Built-in tools are implemented under `claude_code.tools` and registered through `claude_code.core.tools_registry`. MCP tools are merged at runtime (see [ARCHITECTURE.md](./ARCHITECTURE.md)).

## Base types

| Module | Types | Purpose |
|--------|--------|---------|
| `claude_code.tools.base` | `Tool`, `ToolResult`, `ToolUseContext`, `ToolPermissionContext`, `ToolValidationResult` | **Concrete** tool implementations (Pydantic input models, `validate_input`, async `execute`). |
| `claude_code.core.tool` | `Tool` (ABC), `ToolUseContext`, `ToolPermissionContext`, `AppState`, progress dataclasses | **Registry / Anthropic** integration layer; used by `tools_registry` and `core.query_engine`. |

When adding a tool, follow an existing tool’s pattern and check which base class it subclasses.

## Registry API

| Function | Description |
|----------|-------------|
| `get_all_base_tools()` | Lazy-imports and caches all built-in tool instances. |
| `get_tools(permission_context)` | Applies simple mode, REPL hiding, deny rules, `is_enabled()`. |
| `assemble_tool_pool(permission_context, mcp_tools)` | Built-ins + MCP, sorted, deduped (built-ins win). |
| `filter_tools_by_deny_rules(tools, ctx)` | Removes blanket-denied tools. |
| `get_deny_rule_for_tool(ctx, tool)` | Inspects `always_deny_rules` including `mcp__` prefix rules. |

## Environment flags affecting the tool pool

| Variable | When truthy (`true`/`1`/`yes`) |
|----------|-------------------------------|
| `CLAUDE_CODE_SIMPLE` | Only shell + read + str-replace (+ optional `REPL`); coordinator adds `Task`, `TaskStop`, `SendMessage`. |
| `CLAUDE_CODE_REPL_MODE` | If `REPL` tool present, hides `Shell`, `Read`, `StrReplace`, `Write`, `Glob`, `Grep` as standalone tools. |
| `CLAUDE_CODE_TODO_V2` | Adds `TaskCreate`, `TaskGet`, `TaskUpdate`, `TaskList`. |
| `CLAUDE_CODE_TOOL_SEARCH` | Adds `ToolSearch`. |
| `CLAUDE_CODE_EMBEDDED_SEARCH` | Omits standalone `Glob` and `Grep`. |
| `CLAUDE_CODE_COORDINATOR_MODE` | Adds coordinator tools in simple mode (see registry). |

## Policy sets (registry constants)

These **string names** are used for agent/coordinator policy (not always identical to every tool’s `name` property):

- `ALL_AGENT_DISALLOWED_TOOLS`: `SendMessage`, `TeamCreate`, `TeamDelete`, `TodoWrite`
- `CUSTOM_AGENT_DISALLOWED_TOOLS`: `TaskCreate`, `TaskUpdate`, `TaskList`, `TaskGet`, `TaskStop`, `TaskOutput`
- `ASYNC_AGENT_ALLOWED_TOOLS`: shell/read/write-style tools, web, notebook, `Skill`, `Config`, `SendMessage`, `Brief`
- `COORDINATOR_MODE_ALLOWED_TOOLS`: `Task`, `TaskStop`, `TaskOutput`, `SendMessage`, `Read`, `Glob`, `Grep`, `Brief`

## Built-in tools loaded by `get_all_base_tools_impl`

The registry attempts (lazy) imports in this order (some may be skipped if `ImportError` or flags disable them):

| Order | Import path | Typical public name (check `name` property) |
|-------|-------------|---------------------------------------------|
| 1 | `tools.agent.AgentTool` | `Task` |
| 2 | `tools.task_output.TaskOutputTool` | (task output) |
| 3 | `tools.bash.BashTool` | `Shell` (`BASH_TOOL_NAME`) |
| 4–5 | `GlobTool`, `GrepTool` | `Glob`, `Grep` — skipped if `CLAUDE_CODE_EMBEDDED_SEARCH` |
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
| 16 | Task tools if `CLAUDE_CODE_TODO_V2` | `TaskCreate`, … |
| 17 | `ListMcpResourcesTool`, `ReadMcpResourceTool` | MCP resource discovery |
| 18 | `ToolSearchTool` if `CLAUDE_CODE_TOOL_SEARCH` | `ToolSearch` |

> **Note:** Internal policy lists sometimes say `Bash` / `Edit`; the **implemented** names for bash and file edit are **`Shell`** and **`StrReplace`** (see `tools/bash/prompt.py`, `tools/file_edit/prompt.py`).

## Tool modules in `claude_code.tools.__init__`

The package aggregates many tool submodules for tests and dynamic loading, including:

`agent_tool`, `bash_tool`, `brief_tool`, `config_tool`, `file_edit_tool`, `file_read_tool`, `file_search_tool`, `file_write_tool`, `glob_tool`, `grep_tool`, `image_tool`, `list_code_definition_tool`, `list_dir_tool`, `lsp_tool`, `mcp_tool`, `memory_tool`, `multi_edit_tool`, `notebook_edit_tool`, `notebook_tool`, `parallel_tool`, `plan_mode`, `powershell_tool`, `read_file_tool`, `remote_trigger_tool`, `schedule_cron`, `search_tool`, `shell_tool`, `skill_tool`, `sleep_tool`, `sub_agent_tool`, `switch_mode_tool`, `task_create_tool`, `task_tool`, `task_tools`, `task_update_tool`, `team_create`, `team_create_tool`, `think_tool`, `todo_read_tool`, `todo_write_tool`, `web_fetch_tool`, `web_search_tool`, `worktree`, `write_file_tool`, …

Not every module is wired into `get_all_base_tools_impl`; some are used by alternate code paths or future parity.

## Example: defining tool input with Pydantic

Pattern from `tools/bash/tool.py`:

```python
from pydantic import BaseModel, Field

class BashInput(BaseModel):
    command: str = Field(..., description="The bash command to execute.")
    timeout: int | None = Field(None, description="Timeout in milliseconds.")
    run_in_background: bool = Field(False)
    working_directory: str | None = Field(None)

class BashTool(Tool[BashInput, BashOutput]):
    @property
    def name(self) -> str:
        return BASH_TOOL_NAME  # "Shell"

    def get_input_schema(self) -> dict[str, object]:
        return BashInput.model_json_schema()
```

## MCP deny rule pattern

Blanket deny for a whole MCP server prefix uses patterns like `mcp__servername__…` matched against `mcp_info["serverName"]` — see `get_deny_rule_for_tool` in `tools_registry.py`.

## Related configuration

- File read output limits: `CLAUDE_CODE_FILE_READ_MAX_OUTPUT_TOKENS` (`tools/file_read/limits.py`).
- Tool concurrency: `CLAUDE_CODE_MAX_TOOL_USE_CONCURRENCY` (`services/tools/orchestration.py`).

## Related documents

- [ARCHITECTURE.md](./ARCHITECTURE.md)
- [DATA_FLOW.md](./DATA_FLOW.md)
- [SERVICES.md](./SERVICES.md) (MCP services)
