"""
Incremental turn-based file diff aggregation from messages.

Migrated from: hooks/useTurnDiffs.ts
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any


@dataclass
class PatchHunk:
    old_start: int
    old_lines: int
    new_start: int
    new_lines: int
    lines: list[str]


@dataclass
class TurnFileDiff:
    file_path: str
    hunks: list[PatchHunk]
    is_new_file: bool
    lines_added: int
    lines_removed: int


@dataclass
class TurnDiff:
    turn_index: int
    user_prompt_preview: str
    timestamp: str
    files: dict[str, TurnFileDiff]
    stats: dict[str, int]


def _count_hunk_lines(hunks: Sequence[PatchHunk]) -> tuple[int, int]:
    added = removed = 0
    for h in hunks:
        for line in h.lines:
            if line.startswith("+"):
                added += 1
            elif line.startswith("-"):
                removed += 1
    return added, removed


def _user_prompt_preview(message: Mapping[str, Any]) -> str:
    if message.get("type") != "user":
        return ""
    m = message.get("message")
    if not isinstance(m, Mapping):
        return ""
    c = m.get("content")
    text = str(c) if isinstance(c, str) else ""
    return text if len(text) <= 30 else text[:29] + "…"


def _is_file_edit_result(result: Mapping[str, Any]) -> bool:
    fp = result.get("filePath")
    sp = result.get("structuredPatch")
    typ = result.get("type")
    content = result.get("content")
    has_patch = isinstance(sp, list) and len(sp) > 0
    is_new = typ == "create" and isinstance(content, str)
    return isinstance(fp, str) and (has_patch or is_new)


def _hunks_from_structured(sp: Sequence[Mapping[str, Any]]) -> list[PatchHunk]:
    out: list[PatchHunk] = []
    for h in sp:
        lines = h.get("lines")
        if not isinstance(lines, list):
            lines = []
        out.append(
            PatchHunk(
                old_start=int(h.get("oldStart", 0)),
                old_lines=int(h.get("oldLines", 0)),
                new_start=int(h.get("newStart", 0)),
                new_lines=int(h.get("newLines", 0)),
                lines=[str(x) for x in lines],
            )
        )
    return out


@dataclass
class TurnDiffCache:
    completed_turns: list[TurnDiff] = field(default_factory=list)
    current_turn: TurnDiff | None = None
    last_processed_index: int = 0
    last_turn_index: int = 0


def compute_turn_diffs(
    messages: Sequence[Mapping[str, Any]],
    cache: TurnDiffCache,
) -> list[TurnDiff]:
    if len(messages) < cache.last_processed_index:
        cache.completed_turns.clear()
        cache.current_turn = None
        cache.last_processed_index = 0
        cache.last_turn_index = 0

    for i in range(cache.last_processed_index, len(messages)):
        message = messages[i]
        if message.get("type") != "user":
            continue
        m_inner = message.get("message")
        content0: Mapping[str, Any] | None = None
        if isinstance(m_inner, Mapping):
            c = m_inner.get("content")
            if isinstance(c, list) and c and isinstance(c[0], Mapping):
                content0 = c[0]
        is_tool_result = bool(message.get("toolUseResult")) or (
            content0 is not None and content0.get("type") == "tool_result"
        )
        is_meta = bool(message.get("isMeta"))
        if not is_tool_result and not is_meta:
            if cache.current_turn and cache.current_turn.files:
                _finalize_stats(cache.current_turn)
                cache.completed_turns.append(cache.current_turn)
            cache.last_turn_index += 1
            cache.current_turn = TurnDiff(
                turn_index=cache.last_turn_index,
                user_prompt_preview=_user_prompt_preview(message),
                timestamp=str(message.get("timestamp", "")),
                files={},
                stats={"filesChanged": 0, "linesAdded": 0, "linesRemoved": 0},
            )
        elif cache.current_turn and message.get("toolUseResult"):
            tr = message["toolUseResult"]
            if isinstance(tr, Mapping) and _is_file_edit_result(tr):
                fp = str(tr["filePath"])
                sp_raw = tr.get("structuredPatch")
                sp_list = [x for x in sp_raw if isinstance(x, Mapping)] if isinstance(sp_raw, list) else []
                hunks = _hunks_from_structured(sp_list)
                is_new = tr.get("type") == "create"
                entry = cache.current_turn.files.get(fp)
                if entry is None:
                    entry = TurnFileDiff(
                        file_path=fp,
                        hunks=[],
                        is_new_file=bool(is_new),
                        lines_added=0,
                        lines_removed=0,
                    )
                    cache.current_turn.files[fp] = entry
                if is_new and len(hunks) == 0 and isinstance(tr.get("content"), str):
                    content = str(tr["content"])
                    lines = content.split("\n")
                    syn = PatchHunk(
                        old_start=0,
                        old_lines=0,
                        new_start=1,
                        new_lines=len(lines),
                        lines=["+" + ln for ln in lines],
                    )
                    entry.hunks.append(syn)
                    entry.lines_added += len(lines)
                else:
                    entry.hunks.extend(hunks)
                    a, r = _count_hunk_lines(hunks)
                    entry.lines_added += a
                    entry.lines_removed += r
                if is_new:
                    entry.is_new_file = True

    cache.last_processed_index = len(messages)
    out = list(cache.completed_turns)
    if cache.current_turn and cache.current_turn.files:
        _finalize_stats(cache.current_turn)
        out.append(cache.current_turn)
    return list(reversed(out))


def _finalize_stats(turn: TurnDiff) -> None:
    ta = tr = 0
    for f in turn.files.values():
        ta += f.lines_added
        tr += f.lines_removed
    turn.stats = {"filesChanged": len(turn.files), "linesAdded": ta, "linesRemoved": tr}
