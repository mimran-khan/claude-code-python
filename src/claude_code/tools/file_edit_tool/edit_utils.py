"""String edit helpers migrated from tools/FileEditTool/utils.ts."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Protocol

from .types import FileEditRecord, StructuredPatchHunk


class _PatchHunkLike(Protocol):
    """StructuredPatchHunk from ``utils.diff`` or ``tools.file_edit_tool.types``."""

    lines: list[str]


def get_edits_for_patch(patch: Sequence[_PatchHunkLike]) -> list[FileEditRecord]:
    """
    Reconstruct FileEdit records from structured patch hunks.

    Migrated from: tools/FileEditTool/utils.ts (getEditsForPatch)
    """
    edits: list[FileEditRecord] = []
    for hunk in patch:
        old_lines: list[str] = []
        new_lines: list[str] = []
        for line in hunk.lines:
            if line.startswith(" "):
                body = line[1:]
                old_lines.append(body)
                new_lines.append(body)
            elif line.startswith("-"):
                old_lines.append(line[1:])
            elif line.startswith("+"):
                new_lines.append(line[1:])
        edits.append(
            FileEditRecord(
                old_string="\n".join(old_lines),
                new_string="\n".join(new_lines),
                replace_all=False,
            )
        )
    return edits


LEFT_SINGLE_CURLY_QUOTE = "\u2018"
RIGHT_SINGLE_CURLY_QUOTE = "\u2019"
LEFT_DOUBLE_CURLY_QUOTE = "\u201c"
RIGHT_DOUBLE_CURLY_QUOTE = "\u201d"


def normalize_quotes(s: str) -> str:
    return (
        s.replace(LEFT_SINGLE_CURLY_QUOTE, "'")
        .replace(RIGHT_SINGLE_CURLY_QUOTE, "'")
        .replace(LEFT_DOUBLE_CURLY_QUOTE, '"')
        .replace(RIGHT_DOUBLE_CURLY_QUOTE, '"')
    )


def find_actual_string(file_content: str, search_string: str) -> str | None:
    if search_string in file_content:
        return search_string
    normalized_search = normalize_quotes(search_string)
    normalized_file = normalize_quotes(file_content)
    idx = normalized_file.find(normalized_search)
    if idx != -1:
        return file_content[idx : idx + len(search_string)]
    return None


def _is_opening_context(chars: list[str], index: int) -> bool:
    if index == 0:
        return True
    prev = chars[index - 1]
    return prev in (" ", "\t", "\n", "\r", "(", "[", "{", "\u2014", "\u2013")


def _apply_curly_double_quotes(s: str) -> str:
    chars = list(s)
    out: list[str] = []
    for i, ch in enumerate(chars):
        if ch == '"':
            out.append(LEFT_DOUBLE_CURLY_QUOTE if _is_opening_context(chars, i) else RIGHT_DOUBLE_CURLY_QUOTE)
        else:
            out.append(ch)
    return "".join(out)


def _apply_curly_single_quotes(s: str) -> str:
    chars = list(s)
    out: list[str] = []
    for i, ch in enumerate(chars):
        if ch == "'":
            prev = chars[i - 1] if i > 0 else None
            nxt = chars[i + 1] if i + 1 < len(chars) else None
            prev_is_letter = prev is not None and prev.isalpha()
            next_is_letter = nxt is not None and nxt.isalpha()
            if prev_is_letter and next_is_letter:
                out.append(RIGHT_SINGLE_CURLY_QUOTE)
            else:
                out.append(LEFT_SINGLE_CURLY_QUOTE if _is_opening_context(chars, i) else RIGHT_SINGLE_CURLY_QUOTE)
        else:
            out.append(ch)
    return "".join(out)


def preserve_quote_style(old_string: str, actual_old_string: str, new_string: str) -> str:
    if old_string == actual_old_string:
        return new_string
    has_double = LEFT_DOUBLE_CURLY_QUOTE in actual_old_string or RIGHT_DOUBLE_CURLY_QUOTE in actual_old_string
    has_single = LEFT_SINGLE_CURLY_QUOTE in actual_old_string or RIGHT_SINGLE_CURLY_QUOTE in actual_old_string
    if not has_double and not has_single:
        return new_string
    result = new_string
    if has_double:
        result = _apply_curly_double_quotes(result)
    if has_single:
        result = _apply_curly_single_quotes(result)
    return result


def apply_edit_to_file(
    original_content: str,
    old_string: str,
    new_string: str,
    replace_all: bool = False,
) -> str:
    def repl_one(content: str, search: str, replace: str) -> str:
        return content.replace(search, replace, 1)

    def repl_all(content: str, search: str, replace: str) -> str:
        return content.replace(search, replace)

    f: Callable[[str, str, str], str] = repl_all if replace_all else repl_one

    if new_string != "":
        return f(original_content, old_string, new_string)

    with_nl = old_string + "\n"
    strip_trailing_newline = not old_string.endswith("\n") and with_nl in original_content
    if strip_trailing_newline:
        return f(original_content, old_string + "\n", new_string)
    return f(original_content, old_string, new_string)


def get_patch_for_edit(
    file_path: str,
    file_contents: str,
    old_string: str,
    new_string: str,
    replace_all: bool = False,
) -> tuple[list[StructuredPatchHunk], str]:
    """Apply one edit and return (hunks, updated_file)."""
    return get_patch_for_edits(
        file_path,
        file_contents,
        [FileEditRecord(old_string=old_string, new_string=new_string, replace_all=replace_all)],
    )


def get_patch_for_edits(
    file_path: str,
    file_contents: str,
    edits: list[FileEditRecord],
) -> tuple[list[StructuredPatchHunk], str]:
    """
    Apply edits in sequence. Patch hunks are display-only.

    TODO: Port getPatchFromContents from TypeScript utils/diff.js for hunk parity.
    """
    updated_file = file_contents
    applied_new_strings: list[str] = []

    if not file_contents and len(edits) == 1 and edits[0].old_string == "" and edits[0].new_string == "":
        return [], ""

    for edit in edits:
        old_to_check = edit.old_string.rstrip("\n")
        for prev_new in applied_new_strings:
            if old_to_check != "" and old_to_check in prev_new:
                msg = "Cannot edit file: old_string is a substring of a new_string from a previous edit."
                raise ValueError(msg)

        previous = updated_file
        if edit.old_string == "":
            updated_file = edit.new_string
        else:
            updated_file = apply_edit_to_file(
                updated_file,
                edit.old_string,
                edit.new_string,
                edit.replace_all,
            )

        if updated_file == previous:
            raise ValueError("String not found in file. Failed to apply edit.")

        applied_new_strings.append(edit.new_string)

    if updated_file == file_contents:
        raise ValueError("Original and edited file match exactly. Failed to apply edit.")

    # TODO: structured hunks from difflib or diff library matching TS StructuredPatchHunk
    _ = file_path
    return [], updated_file


def are_file_edits_inputs_equivalent(
    file_path_a: str,
    edits_a: list[FileEditRecord],
    file_path_b: str,
    edits_b: list[FileEditRecord],
) -> bool:
    if file_path_a != file_path_b:
        return False
    same = len(edits_a) == len(edits_b) and all(
        a.old_string == b.old_string and a.new_string == b.new_string and a.replace_all == b.replace_all
        for a, b in zip(edits_a, edits_b, strict=True)
    )
    # TODO: semantic equivalence via get_patch_for_edits on file contents (TS parity)
    return same
