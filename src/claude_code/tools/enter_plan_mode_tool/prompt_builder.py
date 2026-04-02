"""Prompt text for the enter-plan-mode tool."""


def get_enter_plan_mode_tool_prompt() -> str:
    return (
        "Requests permission to enter plan mode so the agent can explore requirements "
        "and design an approach before writing code."
    )
