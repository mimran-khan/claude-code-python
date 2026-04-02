"""Search and select deferred tools by name or keywords."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from ...core.tool import Tool, ToolCallProgress, ToolResult, ToolUseContext
from .prompt import TOOL_SEARCH_TOOL_NAME, get_tool_search_prompt, is_deferred_tool_record


@dataclass
class ToolSearchInput:
    query: str
    max_results: int = 5


@dataclass
class ToolSearchOutput:
    matches: list[str]
    query: str
    total_deferred_tools: int
    pending_mcp_servers: list[str] | None = None


def _tool_name(tool: Any) -> str:
    if isinstance(tool, dict):
        return str(tool.get("name", ""))
    return str(getattr(tool, "name", ""))


def _tool_hint(tool: Any) -> str:
    if isinstance(tool, dict):
        return str(tool.get("search_hint") or "")
    return str(getattr(tool, "search_hint", None) or "")


def _tool_prompt_async_placeholder(tool: Any) -> str:
    if isinstance(tool, dict):
        return str(tool.get("prompt_text") or tool.get("description") or "")
    return str(getattr(tool, "description", "") or "")


def find_tool_by_name(tools: list[Any], name: str) -> Any | None:
    n = name.strip()
    for t in tools:
        if _tool_name(t) == n:
            return t
        aliases = t.get("aliases", []) if isinstance(t, dict) else getattr(t, "aliases", []) or []
        if n in aliases:
            return t
    return None


def _normalize_tools(tools: list[Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for t in tools:
        if isinstance(t, dict):
            out.append(t)
        else:
            out.append(
                {
                    "name": getattr(t, "name", ""),
                    "search_hint": getattr(t, "search_hint", None),
                    "should_defer": getattr(t, "should_defer", False),
                    "is_mcp": getattr(t, "is_mcp", False),
                    "always_load": getattr(t, "always_load", False),
                    "description": getattr(t, "description", ""),
                },
            )
    return out


def parse_tool_name(name: str) -> tuple[list[str], str, bool]:
    if name.startswith("mcp__"):
        without = name.replace("mcp__", "", 1).lower()
        parts: list[str] = []
        for seg in without.split("__"):
            parts.extend(seg.split("_"))
        parts = [p for p in parts if p]
        full = without.replace("__", " ").replace("_", " ")
        return parts, full, True
    parts = re.sub(r"([a-z])([A-Z])", r"\1 \2", name).replace("_", " ").lower().split()
    parts = [p for p in parts if p]
    return parts, " ".join(parts), False


def _compile_terms(terms: list[str]) -> dict[str, re.Pattern[str]]:
    return {t: re.compile(rf"\b{re.escape(t)}\b") for t in terms}


async def search_tools_with_keywords(
    query: str,
    deferred: list[dict[str, Any]],
    all_tools: list[dict[str, Any]],
    max_results: int,
) -> list[str]:
    q = query.lower().strip()
    if not q:
        return []

    exact = next((t for t in deferred if _tool_name(t).lower() == q), None)
    if not exact:
        exact = next((t for t in all_tools if _tool_name(t).lower() == q), None)
    if exact:
        return [_tool_name(exact)]

    if q.startswith("mcp__") and len(q) > 5:
        pref = [t for t in deferred if _tool_name(t).lower().startswith(q)][:max_results]
        if pref:
            return [_tool_name(t) for t in pref]

    terms = [x for x in q.split() if x]
    required: list[str] = []
    optional: list[str] = []
    for t in terms:
        if t.startswith("+") and len(t) > 1:
            required.append(t[1:])
        else:
            optional.append(t)
    scoring_terms = required + optional if required else terms
    patterns = _compile_terms(scoring_terms)

    candidates = deferred
    if required:

        def matches_required(tool: dict[str, Any]) -> bool:
            parts, _full, _is_m = parse_tool_name(_tool_name(tool))
            desc = _tool_prompt_async_placeholder(tool).lower()
            hint = _tool_hint(tool).lower()
            for term in required:
                pat = patterns[term]
                ok = (
                    term in parts
                    or any(term in p for p in parts)
                    or bool(pat.search(desc))
                    or (bool(hint) and bool(pat.search(hint)))
                )
                if not ok:
                    return False
            return True

        candidates = [t for t in deferred if matches_required(t)]

    scored: list[tuple[str, int]] = []
    for tool in candidates:
        parts, full, is_m = parse_tool_name(_tool_name(tool))
        desc = _tool_prompt_async_placeholder(tool).lower()
        hint = _tool_hint(tool).lower()
        score = 0
        for term in scoring_terms:
            pat = patterns[term]
            if term in parts:
                score += 12 if is_m else 10
            elif any(term in p for p in parts):
                score += 6 if is_m else 5
            elif term in full and score == 0:
                score += 3
            if hint and pat.search(hint):
                score += 4
            if pat.search(desc):
                score += 2
        if score > 0:
            scored.append((_tool_name(tool), score))
    scored.sort(key=lambda x: -x[1])
    return [n for n, _ in scored[:max_results]]


INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "query": {"type": "string"},
        "max_results": {"type": "integer", "default": 5},
    },
    "required": ["query"],
}


class ToolSearchTool(Tool):
    name = TOOL_SEARCH_TOOL_NAME
    description = get_tool_search_prompt()
    input_schema = INPUT_SCHEMA
    is_read_only = True
    is_concurrency_safe = True
    user_facing_name = ""

    async def call(
        self,
        input_data: dict[str, Any],
        context: ToolUseContext,
        progress_callback: ToolCallProgress | None = None,
    ) -> ToolResult[ToolSearchOutput]:
        query = str(input_data.get("query", ""))
        max_results = int(input_data.get("max_results", 5))

        opts = context.options or {}
        tools_raw: list[Any] = list(opts.get("tools", []))
        tools = _normalize_tools(tools_raw)
        deferred = [t for t in tools if is_deferred_tool_record(t)]

        sel = re.match(r"^select:(.+)$", query, re.I)
        if sel:
            requested = [s.strip() for s in sel.group(1).split(",") if s.strip()]
            found: list[str] = []
            for tn in requested:
                t = find_tool_by_name(tools_raw, tn)
                if t:
                    name = _tool_name(t)
                    if name not in found:
                        found.append(name)
            return ToolResult(
                data=ToolSearchOutput(
                    matches=found,
                    query=query,
                    total_deferred_tools=len(deferred),
                ),
            )

        matches = await search_tools_with_keywords(query, deferred, tools, max_results)
        pending: list[str] | None = None
        if not matches and context.get_app_state:
            app = context.get_app_state()
            mcp = app.get("mcp") if isinstance(app, dict) else getattr(app, "mcp", None)
            if isinstance(mcp, dict):
                clients = mcp.get("clients", [])
                pend = [c.get("name") for c in clients if c.get("type") == "pending"]
                pending = [str(n) for n in pend if n]

        return ToolResult(
            data=ToolSearchOutput(
                matches=matches,
                query=query,
                total_deferred_tools=len(deferred),
                pending_mcp_servers=pending,
            ),
        )


def clear_tool_search_description_cache() -> None:
    """Compatibility hook; Python implementation is stateless."""
