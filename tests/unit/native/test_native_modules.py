"""Unit tests for ``claude_code.native`` (color diff, file index)."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from claude_code.native.color_diff import ColorDiff, ColorFile, get_syntax_theme
from claude_code.native.file_index import FileIndex, SearchResult, _score_path


def test_get_syntax_theme_respects_bat_theme_env() -> None:
    with patch.dict("os.environ", {"BAT_THEME": "MyTheme"}):
        t = get_syntax_theme("dark")
    assert t.theme == "MyTheme"
    assert t.source == "BAT_THEME"


def test_get_syntax_theme_defaults() -> None:
    with patch.dict("os.environ", {}, clear=True):
        assert get_syntax_theme("dark").theme == "OneDark"
        assert get_syntax_theme("light").theme == "OneLight"


def test_color_diff_hunks_and_render() -> None:
    old = ["line1", "line2", "keep"]
    new = ["line1", "line2-changed", "keep"]
    diff = ColorDiff(old, new, context=1)
    hunks = diff.get_hunks()
    assert len(hunks) >= 1
    rendered = diff.render(theme="dark", line_numbers=False, word_diff=False)
    assert "line2-changed" in rendered or "changed" in rendered


def test_color_diff_empty_no_hunks_returns_empty_render() -> None:
    diff = ColorDiff(["a"], ["a"])
    assert diff.render() == ""


def test_color_file_render_and_line_count() -> None:
    cf = ColorFile("one\ntwo\nthree", filepath="x.txt")
    assert cf.line_count == 3
    out = cf.render(line_numbers=True, start_line=1, end_line=2)
    assert "one" in out and "two" in out


def test_score_path_matches_and_misses() -> None:
    assert _score_path("src/foo_bar.py", "fb") is not None
    assert _score_path("src/foo.py", "zzz") is None


@pytest.mark.asyncio
async def test_file_index_search_and_async_load() -> None:
    idx = FileIndex()
    idx.load_from_file_list(["a.py", "b.py", "tests/x.py"])
    assert idx.path_count == 3
    results = idx.search("a", limit=5)
    assert any(r.path == "a.py" for r in results)

    idx2 = FileIndex()
    await idx2.load_from_file_list_async(["z.txt", "y.txt"])
    assert idx2.path_count == 2
    empty_q = idx2.search("", limit=10)
    assert all(isinstance(r, SearchResult) for r in empty_q)

    idx2.clear()
    assert idx2.path_count == 0
