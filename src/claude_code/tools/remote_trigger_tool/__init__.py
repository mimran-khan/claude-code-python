"""Remote trigger tool. Migrated from tools/RemoteTriggerTool/."""

from .prompt_text import DESCRIPTION, PROMPT, REMOTE_TRIGGER_TOOL_NAME
from .remote_trigger_tool_base import RemoteTriggerBaseTool, RemoteTriggerOutput

__all__ = [
    "REMOTE_TRIGGER_TOOL_NAME",
    "DESCRIPTION",
    "PROMPT",
    "RemoteTriggerBaseTool",
    "RemoteTriggerOutput",
]
