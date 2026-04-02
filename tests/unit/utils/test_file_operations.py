"""Unit tests for ``claude_code.utils.file``."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from claude_code.utils.file import (
    convert_leading_tabs_to_spaces,
    detect_file_encoding,
    detect_line_endings,
    detect_line_endings_for_string,
    get_absolute_and_relative_paths,
    get_file_modification_time,
    is_directory,
    is_file,
    is_probably_binary,
    list_directory,
    path_exists,
    read_symlink,
    remove_directory,
    remove_file,
)


def test_is_probably_binary_empty_file(tmp_path) -> None:
    p = tmp_path / "e"
    p.write_bytes(b"")
    assert is_probably_binary(str(p)) is False


def test_is_probably_binary_nul_byte(tmp_path) -> None:
    p = tmp_path / "b"
    p.write_bytes(b"hello\x00world")
    assert is_probably_binary(str(p)) is True


def test_is_probably_binary_high_control_ratio(tmp_path) -> None:
    p = tmp_path / "c"
    p.write_bytes(bytes([0x01] * 100))
    assert is_probably_binary(str(p)) is True


def test_is_probably_binary_oserror_returns_true(tmp_path) -> None:
    with patch("builtins.open", side_effect=PermissionError("no")):
        assert is_probably_binary(str(tmp_path / "ghost")) is True


def test_detect_line_endings_for_string_crlf() -> None:
    assert detect_line_endings_for_string("a\r\nb") == "CRLF"


def test_detect_line_endings_for_string_lf_only() -> None:
    assert detect_line_endings_for_string("a\nb") == "LF"


def test_convert_leading_tabs_no_tabs() -> None:
    s = "  spaces\n"
    assert convert_leading_tabs_to_spaces(s) is s


def test_convert_leading_tabs_expands() -> None:
    assert convert_leading_tabs_to_spaces("\thello") == "  hello"


@pytest.mark.parametrize(
    "bom, expected",
    [
        (b"\xff\xfe\x00\x00", "utf-32-le"),
        (b"\x00\x00\xfe\xff", "utf-32-be"),
        (b"\xff\xfe", "utf-16-le"),
        (b"\xfe\xff", "utf-16-be"),
        (b"\xef\xbb\xbfhi", "utf-8-sig"),
    ],
)
def test_detect_file_encoding_bom(tmp_path, bom: bytes, expected: str) -> None:
    p = tmp_path / "t"
    p.write_bytes(bom + b"rest")
    assert detect_file_encoding(str(p)) == expected


def test_detect_file_encoding_sniff_utf8(tmp_path) -> None:
    p = tmp_path / "u8"
    p.write_bytes("café".encode("utf-8"))
    assert detect_file_encoding(str(p)) in ("utf-8", "utf-8-sig")


def test_detect_line_endings_read_error_returns_lf(tmp_path) -> None:
    with patch("builtins.open", side_effect=OSError("bad")):
        assert detect_line_endings(str(tmp_path / "x")) == "LF"


def test_path_exists_true(tmp_path) -> None:
    f = tmp_path / "a"
    f.write_text("x", encoding="utf-8")
    assert path_exists(str(f)) is True


@pytest.mark.asyncio
async def test_path_exists_async_true(tmp_path) -> None:
    f = tmp_path / "a"
    f.write_text("x", encoding="utf-8")
    from claude_code.utils.file import path_exists_async

    assert await path_exists_async(str(f)) is True


@pytest.mark.asyncio
async def test_path_exists_async_missing() -> None:
    from claude_code.utils.file import path_exists_async

    assert await path_exists_async("/nonexistent/path/xyz123") is False


def test_get_file_modification_time_ms_floor(tmp_path) -> None:
    f = tmp_path / "t"
    f.write_text("a", encoding="utf-8")
    mt = get_file_modification_time(str(f))
    assert isinstance(mt, int)
    assert mt == int(mt)


@pytest.mark.asyncio
async def test_get_file_modification_time_async(tmp_path) -> None:
    from claude_code.utils.file import get_file_modification_time_async

    f = tmp_path / "t"
    f.write_text("a", encoding="utf-8")
    mt = await get_file_modification_time_async(str(f))
    assert mt == int(mt)


def test_get_absolute_and_relative_paths_none() -> None:
    assert get_absolute_and_relative_paths(None) == {
        "absolute_path": None,
        "relative_path": None,
    }


def test_get_absolute_and_relative_paths_resolves(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    with patch("claude_code.utils.cwd.get_cwd", return_value=str(tmp_path)):
        out = get_absolute_and_relative_paths(str(tmp_path / "f"))
    assert out["absolute_path"] is not None
    assert out["relative_path"] is not None


@pytest.mark.asyncio
async def test_ensure_directory_async(tmp_path) -> None:
    from claude_code.utils.file import ensure_directory_async

    d = tmp_path / "nested" / "d"
    await ensure_directory_async(str(d))
    assert d.is_dir()


@pytest.mark.asyncio
async def test_read_write_text_async(tmp_path) -> None:
    from claude_code.utils.file import read_file_async, write_text_content_async

    p = tmp_path / "rw"
    await write_text_content_async(str(p), "line\n", line_endings="LF")
    text = await read_file_async(str(p))
    assert text == "line\n"


@pytest.mark.asyncio
async def test_write_text_content_async_crlf(tmp_path) -> None:
    from claude_code.utils.file import write_text_content_async

    p = tmp_path / "crlf"
    await write_text_content_async(str(p), "a\nb", line_endings="CRLF")
    raw = p.read_bytes()
    assert b"\r\n" in raw


def test_write_text_content_crlf_roundtrip(tmp_path) -> None:
    from claude_code.utils.file import write_text_content

    p = tmp_path / "w"
    write_text_content(str(p), "x\ny", line_endings="CRLF")
    # Text-mode reads normalize newlines; assert on raw bytes.
    assert b"\r\n" in p.read_bytes()


def test_remove_file_success(tmp_path) -> None:
    f = tmp_path / "d"
    f.write_text("z", encoding="utf-8")
    assert remove_file(str(f)) is True
    assert not f.exists()


def test_remove_file_failure_logs() -> None:
    with patch("claude_code.utils.file.os.remove", side_effect=OSError("nope")):
        with patch("claude_code.utils.file.log_error"):
            assert remove_file("/nope/file") is False


def test_remove_directory_recursive(tmp_path) -> None:
    d = tmp_path / "r"
    d.mkdir()
    (d / "f").write_text("1", encoding="utf-8")
    assert remove_directory(str(d), recursive=True) is True


def test_remove_directory_failure() -> None:
    with patch("claude_code.utils.file.os.rmdir", side_effect=OSError("bad")):
        with patch("claude_code.utils.file.log_error"):
            assert remove_directory("/nope", recursive=False) is False


def test_list_directory_error_returns_empty() -> None:
    with patch("claude_code.utils.file.os.listdir", side_effect=PermissionError("no")):
        with patch("claude_code.utils.file.log_error"):
            assert list_directory("/root") == []


def test_is_file_and_is_directory(tmp_path) -> None:
    f = tmp_path / "f"
    f.write_text("x", encoding="utf-8")
    assert is_file(str(f)) is True
    assert is_directory(str(tmp_path)) is True


def test_read_symlink_missing() -> None:
    with patch("claude_code.utils.file.log_error"):
        assert read_symlink("/nonexistent/symlink") is None


def test_read_file_safe_skips_binary(tmp_path) -> None:
    from claude_code.utils.file import read_file_safe

    p = tmp_path / "bin"
    p.write_bytes(b"\x00\x01\x02")
    with patch("claude_code.utils.file.is_probably_binary", return_value=True):
        assert read_file_safe(str(p)) is None
