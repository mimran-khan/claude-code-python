"""
Pretty-print nested dict-like structures as a Unicode tree.

Migrated from: utils/treeify.ts (theme colors omitted; optional ANSI via callback).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Union

TreeNode = dict[str, Union["TreeNode", str, None]]


@dataclass
class TreeifyOptions:
    show_values: bool = True
    hide_functions: bool = False
    use_colors: bool = False
    colorize: Callable[[str, str], str] | None = None
    """If set, (fragment, role) -> colored string; role in tree_char|key|value."""


_BRANCH = "├"
_LAST = "└"
_VERT = "│"
_EMPTY = " "


def treeify(obj: TreeNode, options: TreeifyOptions | None = None) -> str:
    opts = options or TreeifyOptions()
    lines: list[str] = []
    visited: set[int] = set()

    def paint(text: str, role: str) -> str:
        if opts.colorize:
            return opts.colorize(text, role)
        return text

    def grow_branch(
        node: TreeNode | str | Any,
        prefix: str,
        _is_last: bool,
        depth: int = 0,
    ) -> None:
        if isinstance(node, str):
            lines.append(prefix + paint(node, "value"))
            return
        if node is None or isinstance(node, (int, float, bool)):
            if opts.show_values:
                lines.append(prefix + paint(str(node), "value"))
            return
        if not isinstance(node, dict):
            if opts.show_values:
                lines.append(prefix + paint(str(node), "value"))
            return

        nid = id(node)
        if nid in visited:
            lines.append(prefix + paint("[Circular]", "value"))
            return
        visited.add(nid)

        keys = [
            k
            for k in node
            if not (
                opts.hide_functions and callable(node[k])  # type: ignore[arg-type]
            )
        ]
        for index, key in enumerate(keys):
            value = node[key]
            is_last_key = index == len(keys) - 1
            node_prefix = "" if depth == 0 and index == 0 else prefix
            tree_char = _LAST if is_last_key else _BRANCH
            colored_tree = paint(tree_char, "tree_char")
            colored_key = paint(key, "key") if key.strip() else ""
            line = node_prefix + colored_tree + (f" {colored_key}" if colored_key else "")
            should_colon = bool(key.strip())

            if isinstance(value, dict) and value is not node:
                if id(value) in visited:
                    colored_val = paint("[Circular]", "value")
                    sep = ": " if should_colon else (" " if line else "")
                    lines.append(line + sep + colored_val)
                else:
                    lines.append(line)
                    cont = _EMPTY if is_last_key else _VERT
                    colored_cont = paint(cont, "tree_char")
                    next_prefix = node_prefix + colored_cont + " "
                    grow_branch(value, next_prefix, is_last_key, depth + 1)
            elif isinstance(value, list):
                sep = ": " if should_colon else (" " if line else "")
                lines.append(line + sep + paint(f"[Array({len(value)})]", "value"))
            elif opts.show_values:
                vs = "[Function]" if callable(value) else str(value)
                sep = ": " if should_colon else (" " if line else "")
                lines.append(line + sep + paint(vs, "value"))
            else:
                lines.append(line)

    if not obj:
        return paint("(empty)", "value")
    keys = list(obj.keys())
    if len(keys) == 1 and keys[0].strip() == "" and isinstance(obj.get(keys[0]), str):
        k0 = keys[0]
        return paint(_LAST, "tree_char") + " " + paint(str(obj[k0]), "value")

    grow_branch(obj, "", True)
    return "\n".join(lines)
