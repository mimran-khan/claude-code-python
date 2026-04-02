"""Additional unit tests for claude_code.utils.file."""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from claude_code.utils.file import (
    convert_leading_tabs_to_spaces,
    detect_line_endings,
    detect_line_endings_for_string,
    ensure_directory,
    get_absolute_and_relative_paths,
    get_file_size,
    is_directory,
    is_file,
    list_directory,
    path_exists,
    remove_file,
    write_text_content,
)


def test_detect_line_endings_for_string_crlf() -> None:
    assert detect_line_endings_for_string("a\r\nb") == "CRLF"


def test_detect_line_endings_for_string_lf_default() -> None:
    assert detect_line_endings_for_string("a\nb") == "LF"


def test_convert_leading_tabs_to_spaces() -> None:
    assert convert_leading_tabs_to_spaces("\tfoo\n  bar") == "  foo\n  bar"


def test_write_text_content_crlf_normalizes(tmp_path) -> None:
    p = tmp_path / "t.txt"
    write_text_content(str(p), "a\nb", line_endings="CRLF")
    assert p.read_bytes() == b"a\r\nb"


@patch("claude_code.utils.cwd.get_cwd")
@patch("claude_code.utils.file.expand_path")
def test_get_absolute_and_relative_paths(mock_expand, mock_cwd, tmp_path) -> None:
    mock_cwd.return_value = str(tmp_path)
    mock_expand.return_value = str(tmp_path / "sub" / "f.py")
    out = get_absolute_and_relative_paths("sub/f.py")
    assert out["absolute_path"] == str(tmp_path / "sub" / "f.py")
    assert out["relative_path"] == os.path.join("sub", "f.py")


def test_get_absolute_and_relative_paths_none_input() -> None:
    assert get_absolute_and_relative_paths(None) == {
        "absolute_path": None,
        "relative_path": None,
    }


def test_ensure_directory_creates_nested(tmp_path) -> None:
    d = tmp_path / "a" / "b"
    ensure_directory(str(d))
    assert d.is_dir()


def test_path_exists_true_for_file(tmp_path) -> None:
    f = tmp_path / "x"
    f.write_text("h", encoding="utf-8")
    assert path_exists(str(f)) is True


def test_get_file_size_matches_content(tmp_path) -> None:
    f = tmp_path / "s.bin"
    f.write_bytes(b"abcd")
    assert get_file_size(str(f)) == 4


def test_is_file_and_is_directory(tmp_path) -> None:
    f = tmp_path / "f"
    f.write_text("x", encoding="utf-8")
    assert is_file(str(f)) is True
    assert is_directory(str(tmp_path)) is True


def test_list_directory_returns_names(tmp_path) -> None:
    (tmp_path / "a.txt").write_text("x", encoding="utf-8")
    names = list_directory(str(tmp_path))
    assert "a.txt" in names


@patch("claude_code.utils.file.log_error")
def test_remove_file_false_on_error(mock_log, tmp_path) -> None:
    assert remove_file(str(tmp_path / "nope")) is False


def test_detect_line_endings_reads_file(tmp_path) -> None:
    p = tmp_path / "le.txt"
    p.write_bytes(b"line1\r\nline2\r\n")
    assert detect_line_endings(str(p)) == "CRLF"
