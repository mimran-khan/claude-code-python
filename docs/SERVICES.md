# Services reference

`claude_code.services` groups **network clients**, **product integrations**, and **background capabilities** used by the CLI/engine. Many modules are migrated from TypeScript `services/*.ts` and retain parity-oriented names.

## Re-exports from `services.__init__`

The package `__init__` exposes helpers and submodules:

| Symbol / area | Purpose |
|---------------|---------|
| `estimate_tokens`, `count_tokens` | Rough token estimation (`token_estimation.py`). |
| `get_rate_limit_message`, `get_rate_limit_error_message`, `is_rate_limit_error_message` | User-facing rate limit copy (`rate_limit_messages.py`). |
| `send_notification`, `NotificationOptions` | Desktop/terminal notifications (`notifier.py`). |
| `OAuthService`, `generate_code_verifier`, `generate_code_challenge`, `generate_state` | OAuth PKCE helpers (`oauth`). |
| `generate_away_summary` | Away/summary text (`away_summary.py`). |
| `Diagnostic`, `DiagnosticFile`, `DiagnosticTrackingService`, `diagnostic_tracker` | Diagnostics tracking (`diagnostics`). |
| `ClaudeAILimits`, `RateLimitType`, `get_current_limits`, `update_limits`, `is_rate_limited` | Client-side limit state (`limits`). |

Submodules re-exported for direct import: `agent_summary`, `analytics`, `api`, `auth`, `bedrock`, `claude_ai`, `compact`, `docker`, `lsp`, `magic_docs`, `mcp`, `plugins`, `policy_limits`, `prompt_suggestion`, `remote_managed_settings`, `session_memory`, `settings_sync`, `team_memory_sync`, `tips`, `tool_use_summary`.

## `services.api` — Claude / Anthropic HTTP

Central API surface (see `services/api/__init__.py`):

| Export | Role |
|--------|------|
| `get_anthropic_client`, `AnthropicClient`, `ClientConfig`, `APIRequestError` | HTTP client; supports `firstParty`, `bedrock`, `vertex`, `foundry` providers. |
| `query_model`, `query_model_with_streaming`, `get_max_output_tokens_for_model` | Model calls; `StreamEvent`, `QueryResult` dataclasses. |
| Error helpers | `classify_api_error`, `is_prompt_too_long_message`, `PROMPT_TOO_LONG_ERROR_MESSAGE`, etc. |
| `with_retry`, `RetryConfig`, `should_retry`, `get_retry_delay` | Retry policy. |
| `fetch_bootstrap_api`, `fetch_bootstrap_data`, `BootstrapResponse`, `ModelOption` | Bootstrap / model list. |
| `fetch_utilization`, `format_utilization`, `Utilization`, `RateLimit`, `ExtraUsage` | Usage endpoints. |
| `log_api_request`, `log_api_response`, `calculate_cost`, `RequestLogger`, … | Request logging metrics. |
| Grove-related | Subscription / notice helpers (`grove.py`). |

**Default env-backed config** (`services/api/types.py` pattern):

- `ANTHROPIC_API_KEY`
- `ANTHROPIC_BASE_URL` (default `https://api.anthropic.com`)
- `ANTHROPIC_MODEL` (example default `claude-sonnet-4-20250514`)

Submodules: `admin_requests`, `files_api`, `overage_credit_grant`, `prompt_cache_break_detection`, `referral`, `session_ingress`, `dump_prompts`, `ultrareview_quota`, `metrics_opt_out`, `first_token_date`, etc.

## `services.mcp`

MCP **runtime** integration: VS Code SDK bridge, official registry, XAA IDP login, orchestration helpers. Works with types from `claude_code.mcp`.

Notable env flags:

- `CLAUDE_CODE_ENABLE_XAA` — XAA IDP login path.
- `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC` — registry traffic reduction.

## `services.compact`

Context compaction and session memory compaction (long conversation management). Internal branches may check `USER_TYPE == "ant"` for product-specific behavior.

## `services.session_memory` / `extract_memories` / `team_memory_sync`

Memory extraction, session persistence, and team sync hooks.

## `services.lsp`

Language Server Protocol client (`services/lsp/client.py`) — subprocess env inherits `os.environ`.

## `services.plugins` / `settings_sync` / `remote_managed_settings`

Plugin marketplace, settings synchronization, remotely managed settings (may read `ANTHROPIC_API_KEY`).

## `services.prompt_suggestion` / `auto_dream` / `magic_docs` / `tips`

UX and productivity services: prompt suggestions, speculation (`CLAUDE_CODE_ENABLE_SPECULATION`), documentation helpers, tips.

## `services.policy_limits` / `rate_limit`

Org/policy limits and rate limit mocking (`CLAUDE_MOCK_HEADERLESS_429`, `USER_TYPE`).

## `services.bedrock` / `claude_ai` / `auth`

Provider-specific and Claude.ai integration paths.

## `services.docker`

Docker-related helpers for sandboxes or environments.

## `services.analytics` / `notifier`

Analytics pipeline hooks; OS notification delivery (`TERM_PROGRAM` awareness).

## `services.tools`

Tool orchestration — e.g. `CLAUDE_CODE_MAX_TOOL_USE_CONCURRENCY`.

## `services.agent_summary` / `tool_use_summary`

Summaries for agent runs and tool-use transcripts.

## Standalone service modules (not subpackages)

| File | Role |
|------|------|
| `away_summary.py` | Away summary generation. |
| `internal_logging.py` | Internal logging helpers. |
| `prevent_sleep.py` | Prevent system sleep during work. |
| `vcr.py` | Test VCR / recording behavior. |
| `voice.py`, `voice_keyterms.py`, `voice_stream_stt.py` | Voice pipeline pieces. |

## Related documents

- [ARCHITECTURE.md](./ARCHITECTURE.md)
- [DATA_FLOW.md](./DATA_FLOW.md)
- [API.md](./API.md)
