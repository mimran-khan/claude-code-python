"""Line-number formatting for Read tool output (TS addLineNumbers)."""


def add_line_numbers_from_lines(lines: list[str], *, start_line: int = 1) -> str:
    """Format lines with 1-based line numbers (cat -n style)."""
    out: list[str] = []
    for i, line in enumerate(lines):
        n = start_line + i
        text = line.removesuffix("\n").removesuffix("\r")
        out.append(f"{n:6d}\t{text}")
    return "\n".join(out)
