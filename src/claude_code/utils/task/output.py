"""
Task output formatting.

Migrated from: utils/task/outputFormatting.ts + TaskOutput.ts
"""


def format_task_output(
    task_id: str,
    status: str,
    output: str | None = None,
    error: str | None = None,
) -> str:
    """Format task output for display."""
    lines = [f"Task {task_id}: {status}"]

    if output:
        lines.append("")
        lines.append("Output:")
        lines.append(output)

    if error:
        lines.append("")
        lines.append("Error:")
        lines.append(error)

    return "\n".join(lines)


def get_output_summary(output: str, max_length: int = 200) -> str:
    """Get summary of task output.

    Truncates long output with ellipsis.
    """
    if len(output) <= max_length:
        return output

    return output[: max_length - 3] + "..."


def format_progress(
    progress: float,
    label: str | None = None,
    width: int = 40,
) -> str:
    """Format progress bar."""
    filled = int(progress * width)
    bar = "█" * filled + "░" * (width - filled)
    pct = int(progress * 100)

    if label:
        return f"[{bar}] {pct}% - {label}"
    return f"[{bar}] {pct}%"


def merge_outputs(outputs: list[str]) -> str:
    """Merge multiple outputs into one."""
    return "\n---\n".join(outputs)


def extract_last_lines(output: str, n: int = 10) -> str:
    """Extract last N lines from output."""
    lines = output.split("\n")
    return "\n".join(lines[-n:])
