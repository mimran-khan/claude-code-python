"""
Full tool prompt for TodoWrite.

Migrated from: tools/TodoWriteTool/prompt.ts
"""

from __future__ import annotations

# TS imports FILE_EDIT_TOOL_NAME from FileEditTool/constants — Python equivalent is "Edit".
_FILE_EDIT_TOOL_NAME = "Edit"

PROMPT = f"""Use this tool to create and manage a structured task list for your current coding session. This helps you track progress, organize complex tasks, and demonstrate thoroughness to the user.
It also helps the user understand the progress of the task and overall progress of their requests.

## When to Use This Tool
Use this tool proactively in these scenarios:

1. Complex multi-step tasks - When a task requires 3 or more distinct steps or actions
2. Non-trivial and complex tasks - Tasks that require careful planning or multiple operations
3. User explicitly requests todo list - When the user directly asks you to use the todo list
4. User provides multiple tasks - When users provide a list of things to be done (numbered or comma-separated)
5. After receiving new instructions - Immediately capture user requirements as todos
6. When you start working on a task - Mark it as in_progress BEFORE beginning work. Ideally you should only have one todo as in_progress at a time
7. After completing a task - Mark it as completed and add any new follow-up tasks discovered during implementation

## When NOT to Use This Tool

Skip using this tool when:
1. There is only a single, straightforward task
2. The task is trivial and tracking it provides no organizational benefit
3. The task can be completed in less than 3 trivial steps
4. The task is purely conversational or informational

NOTE that you should not use this tool if there is only one trivial task to do. In this case you are better off just doing the task directly.

## Examples of When NOT to Use the Todo List

<example>
User: Can you add a comment to the calculateTotal function to explain what it does?
Assistant: Sure, let me add a comment to the calculateTotal function to explain what it does.
* Uses the {_FILE_EDIT_TOOL_NAME} tool to add a comment to the calculateTotal function *

<reasoning>
The assistant did not use the todo list because this is a single, straightforward task confined to one location in the code.
</reasoning>
</example>

## Task States and Management

1. **Task States**: pending, in_progress, completed — limit ONE in_progress.
2. **Task Management**: Update in real time; mark complete immediately after finishing.
3. **Task Completion**: Only mark completed when fully done.
4. **Task Breakdown**: Provide content (imperative) and activeForm (present continuous).

When in doubt, use this tool. Being proactive with task management demonstrates attentiveness.
"""

DESCRIPTION = (
    "Update the todo list for the current session. To be used proactively and often to track "
    "progress and pending tasks. Make sure that at least one task is in_progress at all times. "
    "Always provide both content (imperative) and activeForm (present continuous) for each task."
)
