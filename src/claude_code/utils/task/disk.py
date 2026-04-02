"""
Task disk output utilities.

Migrated from: utils/task/diskOutput.ts
"""

from pathlib import Path


def get_task_output_dir() -> Path:
    """Get the directory for task outputs."""
    home = Path.home()
    return home / ".claude" / "tasks"


def get_task_output_path(task_id: str) -> Path:
    """Get the path for a task's output file."""
    return get_task_output_dir() / f"{task_id}.output"


def get_task_output_delta(
    task_id: str,
    last_offset: int = 0,
) -> tuple[str, int]:
    """Get new output since last read.

    Returns:
        Tuple of (new_content, new_offset)
    """
    path = get_task_output_path(task_id)

    if not path.exists():
        return "", 0

    try:
        content = path.read_text()
        new_content = content[last_offset:]
        return new_content, len(content)
    except Exception:
        return "", last_offset


def load_task_output(task_id: str) -> str | None:
    """Load full task output from disk."""
    path = get_task_output_path(task_id)

    if not path.exists():
        return None

    try:
        return path.read_text()
    except Exception:
        return None


def save_task_output(task_id: str, output: str) -> bool:
    """Save task output to disk."""
    path = get_task_output_path(task_id)

    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(output)
        return True
    except Exception:
        return False


def append_task_output(task_id: str, content: str) -> bool:
    """Append to task output file."""
    path = get_task_output_path(task_id)

    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a") as f:
            f.write(content)
        return True
    except Exception:
        return False


def clear_task_output(task_id: str) -> bool:
    """Clear task output file."""
    path = get_task_output_path(task_id)

    try:
        if path.exists():
            path.unlink()
        return True
    except Exception:
        return False
