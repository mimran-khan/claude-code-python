"""
Beta session tracing helpers (detailed spans and OTEL events).

Migrated from: utils/telemetry/betaSessionTracing.ts
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import asdict, dataclass, is_dataclass
from typing import Any, Protocol, TypeVar, runtime_checkable

from ...analytics.metadata import sanitize_tool_name
from ...bootstrap.state import get_is_non_interactive_session
from ...services.analytics.growthbook import get_feature_value_cached
from ...types.message import AssistantMessage, TextBlock, ToolResultBlock, UserMessage
from ..env_utils import is_env_truthy
from .events import schedule_log_otel_event


@runtime_checkable
class SpanLike(Protocol):
    def set_attribute(self, key: str, value: Any) -> None: ...

    def set_attributes(self, attrs: dict[str, Any]) -> None: ...


TSpan = TypeVar("TSpan", bound=SpanLike)

_seen_hashes: set[str] = set()
_last_reported_message_hash: dict[str, str] = {}

MAX_CONTENT_SIZE = 60 * 1024

SYSTEM_REMINDER_REGEX = re.compile(
    r"^<system-reminder>\n?([\s\S]*?)\n?</system-reminder>$",
)


def clear_beta_tracing_state() -> None:
    _seen_hashes.clear()
    _last_reported_message_hash.clear()


def is_beta_tracing_enabled() -> bool:
    base = is_env_truthy(os.environ.get("ENABLE_BETA_TRACING_DETAILED")) and bool(
        os.environ.get("BETA_TRACING_ENDPOINT"),
    )
    if not base:
        return False
    if os.environ.get("USER_TYPE") != "ant":
        return get_is_non_interactive_session() or bool(
            get_feature_value_cached("tengu_trace_lantern", False),
        )
    return True


def truncate_content(
    content: str,
    max_size: int = MAX_CONTENT_SIZE,
) -> tuple[str, bool]:
    if len(content) <= max_size:
        return content, False
    return content[:max_size] + "\n\n[TRUNCATED - Content exceeds 60KB limit]", True


def _short_hash(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()[:12]


def _hash_system_prompt(system_prompt: str) -> str:
    return f"sp_{_short_hash(system_prompt)}"


def _message_content_json(message: UserMessage | AssistantMessage) -> str:
    return json.dumps(message.content, default=_json_default)


def _json_default(obj: object) -> object:
    if isinstance(obj, (UserMessage, AssistantMessage)):
        return {"role": obj.role, "content": obj.content}
    if is_dataclass(obj) and not isinstance(obj, type):
        return asdict(obj)
    raise TypeError(type(obj))


def _hash_message(message: UserMessage | AssistantMessage) -> str:
    return f"msg_{_short_hash(_message_content_json(message))}"


def _extract_system_reminder_content(text: str) -> str | None:
    m = SYSTEM_REMINDER_REGEX.match(text.strip())
    if m:
        return m.group(1).strip()
    return None


def _format_messages_for_context(messages: list[UserMessage]) -> tuple[list[str], list[str]]:
    context_parts: list[str] = []
    system_reminders: list[str] = []

    for message in messages:
        content = message.content
        if isinstance(content, str):
            inner = _extract_system_reminder_content(content)
            if inner is not None:
                system_reminders.append(inner)
            else:
                context_parts.append(f"[USER]\n{content}")
        elif isinstance(content, list):
            for block in content:
                if isinstance(block, TextBlock):
                    inner = _extract_system_reminder_content(block.text)
                    if inner is not None:
                        system_reminders.append(inner)
                    else:
                        context_parts.append(f"[USER]\n{block.text}")
                elif isinstance(block, ToolResultBlock):
                    result_content = block.content if isinstance(block.content, str) else json.dumps(block.content)
                    inner = _extract_system_reminder_content(result_content)
                    if inner is not None:
                        system_reminders.append(inner)
                    else:
                        tool_hdr = f"[TOOL RESULT: {block.tool_use_id}]"
                        context_parts.append(f"{tool_hdr}\n{result_content}")
                elif isinstance(block, dict):
                    btype = block.get("type")
                    if btype == "text":
                        t = str(block.get("text", ""))
                        inner = _extract_system_reminder_content(t)
                        if inner is not None:
                            system_reminders.append(inner)
                        else:
                            context_parts.append(f"[USER]\n{t}")
                    elif btype == "tool_result":
                        rc = block.get("content", "")
                        result_content = rc if isinstance(rc, str) else json.dumps(rc)
                        tid = str(block.get("tool_use_id", ""))
                        inner = _extract_system_reminder_content(result_content)
                        if inner is not None:
                            system_reminders.append(inner)
                        else:
                            context_parts.append(f"[TOOL RESULT: {tid}]\n{result_content}")

    return context_parts, system_reminders


@dataclass
class LLMRequestNewContext:
    system_prompt: str | None = None
    query_source: str | None = None
    tools: str | None = None


def add_beta_interaction_attributes(span: SpanLike, user_prompt: str) -> None:
    if not is_beta_tracing_enabled():
        return
    truncated_prompt, truncated = truncate_content(f"[USER PROMPT]\n{user_prompt}")
    attrs: dict[str, Any] = {"new_context": truncated_prompt}
    if truncated:
        attrs["new_context_truncated"] = True
        attrs["new_context_original_length"] = len(user_prompt)
    span.set_attributes(attrs)


def add_beta_llm_request_attributes(
    span: SpanLike,
    new_context: LLMRequestNewContext | None = None,
    messages_for_api: list[UserMessage | AssistantMessage] | None = None,
) -> None:
    if not is_beta_tracing_enabled():
        return

    if new_context and new_context.system_prompt:
        prompt_hash = _hash_system_prompt(new_context.system_prompt)
        preview = new_context.system_prompt[:500]
        span.set_attribute("system_prompt_hash", prompt_hash)
        span.set_attribute("system_prompt_preview", preview)
        span.set_attribute("system_prompt_length", len(new_context.system_prompt))
        if prompt_hash not in _seen_hashes:
            _seen_hashes.add(prompt_hash)
            truncated_prompt, truncated = truncate_content(new_context.system_prompt)
            meta: dict[str, str | None] = {
                "system_prompt_hash": prompt_hash,
                "system_prompt": truncated_prompt,
                "system_prompt_length": str(len(new_context.system_prompt)),
            }
            if truncated:
                meta["system_prompt_truncated"] = "true"
            schedule_log_otel_event("system_prompt", meta)

    if new_context and new_context.tools:
        try:
            tools_array = json.loads(new_context.tools)
            if not isinstance(tools_array, list):
                raise ValueError("tools must be a list")
            tools_with_hashes: list[dict[str, str]] = []
            for tool in tools_array:
                if not isinstance(tool, dict):
                    continue
                tool_json = json.dumps(tool, sort_keys=True)
                tool_hash = _short_hash(tool_json)
                name = tool.get("name")
                tools_with_hashes.append(
                    {
                        "name": name if isinstance(name, str) else "unknown",
                        "hash": tool_hash,
                        "json": tool_json,
                    },
                )
            span.set_attribute(
                "tools",
                json.dumps([{"name": t["name"], "hash": t["hash"]} for t in tools_with_hashes]),
            )
            span.set_attribute("tools_count", len(tools_with_hashes))
            for item in tools_with_hashes:
                key = f"tool_{item['hash']}"
                if key not in _seen_hashes:
                    _seen_hashes.add(key)
                    truncated_tool, truncated = truncate_content(item["json"])
                    tmeta: dict[str, str | None] = {
                        "tool_name": sanitize_tool_name(item["name"]),
                        "tool_hash": item["hash"],
                        "tool": truncated_tool,
                    }
                    if truncated:
                        tmeta["tool_truncated"] = "true"
                    schedule_log_otel_event("tool", tmeta)
        except (json.JSONDecodeError, ValueError, TypeError):
            span.set_attribute("tools_parse_error", True)

    if messages_for_api and new_context and new_context.query_source:
        query_source = new_context.query_source
        last_hash = _last_reported_message_hash.get(query_source)
        start_index = 0
        if last_hash:
            for i, msg in enumerate(messages_for_api):
                if _hash_message(msg) == last_hash:
                    start_index = i + 1
                    break
        new_messages = [
            m
            for m in messages_for_api[start_index:]
            if isinstance(m, UserMessage) or getattr(m, "role", None) == "user"
        ]
        if new_messages:
            umessages = [m for m in new_messages if isinstance(m, UserMessage)]
            context_parts, system_reminders = _format_messages_for_context(umessages)
            if context_parts:
                full_context = "\n\n---\n\n".join(context_parts)
                truncated_ctx, truncated = truncate_content(full_context)
                attrs: dict[str, Any] = {
                    "new_context": truncated_ctx,
                    "new_context_message_count": len(new_messages),
                }
                if truncated:
                    attrs["new_context_truncated"] = True
                    attrs["new_context_original_length"] = len(full_context)
                span.set_attributes(attrs)
            if system_reminders:
                full_rem = "\n\n---\n\n".join(system_reminders)
                truncated_rem, rem_trunc = truncate_content(full_rem)
                rattrs: dict[str, Any] = {
                    "system_reminders": truncated_rem,
                    "system_reminders_count": len(system_reminders),
                }
                if rem_trunc:
                    rattrs["system_reminders_truncated"] = True
                    rattrs["system_reminders_original_length"] = len(full_rem)
                span.set_attributes(rattrs)
            last_message = messages_for_api[-1]
            _last_reported_message_hash[query_source] = _hash_message(last_message)


def add_beta_llm_response_attributes(
    end_attributes: dict[str, str | int | float | bool],
    metadata: dict[str, Any] | None = None,
) -> None:
    if not is_beta_tracing_enabled() or not metadata:
        return
    model_output = metadata.get("modelOutput")
    if isinstance(model_output, str):
        out, trunc = truncate_content(model_output)
        end_attributes["response.model_output"] = out
        if trunc:
            end_attributes["response.model_output_truncated"] = True
            end_attributes["response.model_output_original_length"] = len(model_output)
    if os.environ.get("USER_TYPE") == "ant":
        thinking = metadata.get("thinkingOutput")
        if isinstance(thinking, str):
            tout, ttrunc = truncate_content(thinking)
            end_attributes["response.thinking_output"] = tout
            if ttrunc:
                end_attributes["response.thinking_output_truncated"] = True
                end_attributes["response.thinking_output_original_length"] = len(thinking)


def add_beta_tool_input_attributes(span: SpanLike, tool_name: str, tool_input: str) -> None:
    if not is_beta_tracing_enabled():
        return
    truncated_input, truncated = truncate_content(f"[TOOL INPUT: {tool_name}]\n{tool_input}")
    attrs: dict[str, Any] = {"tool_input": truncated_input}
    if truncated:
        attrs["tool_input_truncated"] = True
        attrs["tool_input_original_length"] = len(tool_input)
    span.set_attributes(attrs)


def add_beta_tool_result_attributes(
    end_attributes: dict[str, str | int | float | bool],
    tool_name: str | int | bool,
    tool_result: str,
) -> None:
    if not is_beta_tracing_enabled():
        return
    truncated_result, truncated = truncate_content(f"[TOOL RESULT: {tool_name}]\n{tool_result}")
    end_attributes["new_context"] = truncated_result
    if truncated:
        end_attributes["new_context_truncated"] = True
        end_attributes["new_context_original_length"] = len(tool_result)
