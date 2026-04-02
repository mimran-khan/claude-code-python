"""
Tasks module for background task execution.

Provides task types for running shell commands, agents, workflows, etc.
"""

from .local_main_session_task import (
    MainSessionAgentStub,
    complete_main_session_task,
    generate_main_session_task_id,
    register_main_session_task,
)
from .pill_label import get_pill_label, pill_needs_cta
from .stop_task import StopTaskError, is_local_shell_task, stop_task
from .task import (
    LocalShellSpawnInput,
    SetAppState,
    Task,
    TaskContext,
    TaskHandle,
    TaskStateBase,
    TaskStatus,
    TaskType,
    create_task_state_base,
    generate_task_id,
    get_all_tasks,
    get_task_by_type,
    get_task_output_path,
    is_terminal_task_status,
    register_task,
)
from .types import TaskConfig, TaskResult, TaskState, is_background_task

__all__ = [
    # Types
    "Task",
    "TaskType",
    "TaskStatus",
    "TaskHandle",
    "TaskContext",
    "TaskStateBase",
    "LocalShellSpawnInput",
    "SetAppState",
    # Functions
    "is_terminal_task_status",
    "generate_task_id",
    "get_task_output_path",
    "create_task_state_base",
    "register_task",
    "get_all_tasks",
    "get_task_by_type",
    "get_pill_label",
    "pill_needs_cta",
    "stop_task",
    "StopTaskError",
    "is_local_shell_task",
    "register_main_session_task",
    "complete_main_session_task",
    "generate_main_session_task_id",
    "MainSessionAgentStub",
    "TaskConfig",
    "TaskResult",
    "TaskState",
    "is_background_task",
]
