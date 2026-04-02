"""Unit tests for ``claude_code.history``."""

from __future__ import annotations

from pathlib import Path

from claude_code.history import (
    History,
    HistoryEntry,
    PastedContent,
    format_image_ref,
    format_pasted_text_ref,
    get_pasted_text_ref_num_lines,
    parse_references,
)


def test_get_pasted_text_ref_num_lines_counts_newlines() -> None:
    assert get_pasted_text_ref_num_lines("one") == 0
    assert get_pasted_text_ref_num_lines("a\nb\nc") == 2
    assert get_pasted_text_ref_num_lines("x\r\ny") == 1


def test_format_pasted_text_ref_with_and_without_extra_lines() -> None:
    assert format_pasted_text_ref(3, 0) == "[Pasted text #3]"
    assert format_pasted_text_ref(3, 2) == "[Pasted text #3 +2 lines]"


def test_format_image_ref() -> None:
    assert format_image_ref(9) == "[Image #9]"


def test_parse_references_extracts_ids_and_skips_zero() -> None:
    text = "See [Pasted text #1] and [Image #2 +4 lines] plus [Pasted text #0] end."
    refs = parse_references(text)
    ids = sorted(r.id for r in refs)
    assert ids == [1, 2]
    assert all(r.match in text for r in refs)


def test_history_load_save_roundtrip(tmp_path: Path) -> None:
    path = tmp_path / "hist.jsonl"
    h = History(history_path=str(path))
    entry = HistoryEntry(
        prompt="hello",
        pasted_content=[
            PastedContent(id=1, type="text", content="body"),
        ],
        timestamp="t1",
        session_id="s1",
        project_root="/proj",
    )
    h.add(entry)

    h2 = History(history_path=str(path))
    recent = h2.get_recent(5)
    assert len(recent) == 1
    assert recent[0].prompt == "hello"
    assert recent[0].pasted_content[0].id == 1


def test_history_trims_to_max_items(tmp_path: Path) -> None:
    path = tmp_path / "many.jsonl"
    h = History(history_path=str(path))
    for i in range(105):
        h.add(HistoryEntry(prompt=f"p{i}"))
    h.load()
    assert len(h._entries) == 100  # noqa: SLF001 — inspecting internal cap
    assert h._entries[0].prompt == "p5"


def test_history_search_is_case_insensitive(tmp_path: Path) -> None:
    path = tmp_path / "search.jsonl"
    h = History(history_path=str(path))
    h.add(HistoryEntry(prompt="Alpha Beta"))
    matches = h.search("alpha")
    assert len(matches) == 1


def test_history_skips_invalid_json_lines(tmp_path: Path) -> None:
    path = tmp_path / "bad.jsonl"
    path.write_text('{"prompt":"ok"}\nnot-json\n', encoding="utf-8")
    h = History(history_path=str(path))
    h.load()
    assert len(h._entries) == 1  # noqa: SLF001


def test_history_missing_file_loads_empty(tmp_path: Path) -> None:
    path = tmp_path / "missing.jsonl"
    h = History(history_path=str(path))
    h.load()
    assert h.get_recent(3) == []
