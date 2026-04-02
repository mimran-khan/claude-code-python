"""Team create prompt. Migrated from tools/TeamCreateTool/prompt.ts (getPrompt)."""


def get_team_create_prompt() -> str:
    return """
# TeamCreate

## When to Use

Use this tool proactively whenever:
- The user explicitly asks to use a team, swarm, or group of agents
- The user mentions wanting agents to work together, coordinate, or collaborate
- A task is complex enough that it would benefit from parallel work by multiple agents

When in doubt about whether a task warrants a team, prefer spawning a team.

## Choosing Agent Types for Teammates

When spawning teammates via the Agent tool, choose the `subagent_type` based on what tools the agent needs for its task.

Create a new team to coordinate multiple agents working on a project. Teams have a 1:1 correspondence with task lists (Team = TaskList).

```json
{"team_name": "my-project", "description": "Working on feature X"}
```

This creates:
- A team file at `~/.claude/teams/{team-name}/config.json`
- A corresponding task list directory at `~/.claude/tasks/{team-name}/`

## Team Workflow

1. **Create a team** with TeamCreate
2. **Create tasks** using Task tools
3. **Spawn teammates** using the Agent tool with `team_name` and `name`
4. **Assign tasks** using TaskUpdate with `owner`
5. **Teammates work** on assigned tasks and mark them completed via TaskUpdate
6. **Shutdown** via SendMessage with `message: {type: "shutdown_request"}` when done
""".strip()
