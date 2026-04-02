"""XML tag names used in Claude Code messages and communication."""

# XML tag names used to mark skill/command metadata in messages
COMMAND_NAME_TAG = "command-name"
COMMAND_MESSAGE_TAG = "command-message"
COMMAND_ARGS_TAG = "command-args"

# XML tag names for terminal/bash command input and output in user messages
# These wrap content that represents terminal activity, not actual user prompts
BASH_INPUT_TAG = "bash-input"
BASH_STDOUT_TAG = "bash-stdout"
BASH_STDERR_TAG = "bash-stderr"
LOCAL_COMMAND_STDOUT_TAG = "local-command-stdout"
LOCAL_COMMAND_STDERR_TAG = "local-command-stderr"
LOCAL_COMMAND_CAVEAT_TAG = "local-command-caveat"

# All terminal-related tags that indicate a message is terminal output, not a user prompt
TERMINAL_OUTPUT_TAGS = (
    BASH_INPUT_TAG,
    BASH_STDOUT_TAG,
    BASH_STDERR_TAG,
    LOCAL_COMMAND_STDOUT_TAG,
    LOCAL_COMMAND_STDERR_TAG,
    LOCAL_COMMAND_CAVEAT_TAG,
)

TICK_TAG = "tick"

# XML tag names for task notifications (background task completions)
TASK_NOTIFICATION_TAG = "task-notification"
TASK_ID_TAG = "task-id"
TOOL_USE_ID_TAG = "tool-use-id"
TASK_TYPE_TAG = "task-type"
OUTPUT_FILE_TAG = "output-file"
STATUS_TAG = "status"
SUMMARY_TAG = "summary"
REASON_TAG = "reason"
WORKTREE_TAG = "worktree"
WORKTREE_PATH_TAG = "worktreePath"
WORKTREE_BRANCH_TAG = "worktreeBranch"

# XML tag names for ultraplan mode (remote parallel planning sessions)
ULTRAPLAN_TAG = "ultraplan"

# XML tag name for remote /review results (teleported review session output)
REMOTE_REVIEW_TAG = "remote-review"

# run_hunt.sh's heartbeat echoes the orchestrator's progress.json inside this
# tag every ~10s. Local poller parses the latest for the task-status line.
REMOTE_REVIEW_PROGRESS_TAG = "remote-review-progress"

# XML tag name for teammate messages (swarm inter-agent communication)
TEAMMATE_MESSAGE_TAG = "teammate-message"

# XML tag name for external channel messages
CHANNEL_MESSAGE_TAG = "channel-message"
CHANNEL_TAG = "channel"

# XML tag name for cross-session UDS messages (another Claude session's inbox)
CROSS_SESSION_MESSAGE_TAG = "cross-session-message"

# XML tag wrapping the rules/format boilerplate in a fork child's first message
FORK_BOILERPLATE_TAG = "fork-boilerplate"
# Prefix before the directive text, stripped by the renderer
FORK_DIRECTIVE_PREFIX = "Your directive: "

# Common argument patterns for slash commands that request help
COMMON_HELP_ARGS = ["help", "-h", "--help"]

# Common argument patterns for slash commands that request current state/info
COMMON_INFO_ARGS = [
    "list",
    "show",
    "display",
    "current",
    "view",
    "get",
    "check",
    "describe",
    "print",
    "version",
    "about",
    "status",
    "?",
]
