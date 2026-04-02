"""Task create prompt. Migrated from tools/TaskCreateTool/prompt.ts."""


def get_task_create_prompt(*, agent_swarms_enabled: bool = False) -> str:
    teammate_context = " and potentially assigned to teammates" if agent_swarms_enabled else ""
    teammate_tips = (
        "- Include enough detail in the description for another agent to understand and complete the task\n"
        "- New tasks are created with status 'pending' and no owner - use TaskUpdate with `owner` to assign them\n"
        if agent_swarms_enabled
        else ""
    )
    return f"""Use this tool to create a structured task list for your current coding session. This helps you track progress, organize complex tasks, and demonstrate thoroughness to the user.
It also helps the user understand the progress of the task and overall progress of their requests.

## When to Use This Tool

Use this tool proactively in these scenarios:

- Complex multi-step tasks - When a task requires 3 or more distinct steps or actions
- Non-trivial and complex tasks - Tasks that require careful planning or multiple operations{teammate_context}
- Plan mode - When using plan mode, create a task list to track the work
- User explicitly requests todo list - When the user directly asks you to use the todo list
- User provides multiple tasks - When users provide a list of things to be done
- After receiving new instructions - Immediately capture user requirements as tasks
- When you start working on a task - Mark it as in_progress BEFORE beginning work
- After completing a task - Mark it as completed and add any new follow-up tasks

## When NOT to Use This Tool

Skip using this tool when:
- There is only a single, straightforward task
- The task is trivial and tracking it provides no organizational benefit
- The task can be completed in less than 3 trivial steps
- The task is purely conversational or informational

## Task Fields

- **subject**: A brief, actionable title in imperative form
- **description**: What needs to be done
- **active_form** (optional): Present continuous form shown in the spinner when in_progress

All tasks are created with status `pending`.

## Tips

- Create tasks with clear, specific subjects that describe the outcome
- After creating tasks, use TaskUpdate to set up dependencies if needed
{teammate_tips}- Check TaskList first to avoid creating duplicate tasks
"""


DESCRIPTION = "Create a new task in the task list"
