"""
Text prompt processing.

Migrated from: utils/processUserInput/processTextPrompt.ts
"""

import re
import uuid
from dataclasses import dataclass
from typing import Any, Literal, Protocol, TypedDict


class TextPromptContext(Protocol):
    """Structural type for objects that expose a working directory."""

    cwd: str | None


class IdeSelectionDict(TypedDict, total=False):
    """IDE selection payload passed into text prompt processing."""

    text: str
    file: str


class PastedContentBlock(TypedDict, total=False):
    """A pasted attachment (image or text) in prompt processing."""

    type: Literal["image", "text"]
    source: Any
    text: str


class ProcessTextPromptResult(TypedDict, total=False):
    """Structured return value from ``process_text_prompt``."""

    messages: list[dict[str, Any]]
    allowed_tools: list[str] | None
    model: str | None


class MentionDict(TypedDict):
    """A single @-mention span extracted from user text."""

    type: Literal["file", "tool", "agent"]
    value: str
    start: int
    end: int


@dataclass
class TextBlock:
    """A block of text content."""

    type: str  # "text", "mention", "code"
    content: str
    metadata: dict[str, Any] | None = None


async def process_text_prompt(
    text: str,
    context: TextPromptContext,
    pasted_contents: list[PastedContentBlock] | None = None,
    ide_selection: IdeSelectionDict | None = None,
) -> ProcessTextPromptResult:
    """Process a text prompt into messages.

    Handles:
    - @ mentions (files, agents, etc.)
    - Code blocks
    - Inline attachments
    - IDE selections

    Args:
        text: The input text
        context: Processing context
        pasted_contents: Any pasted content
        ide_selection: Current IDE selection

    Returns:
        Dict with messages and processing metadata
    """
    result: ProcessTextPromptResult = {
        "messages": [],
        "allowed_tools": None,
        "model": None,
    }

    # Extract mentions
    mentions = extract_mentions(text)

    # Build content blocks
    content_blocks = []

    # Process IDE selection
    if ide_selection and ide_selection.get("text"):
        content_blocks.append(
            {
                "type": "text",
                "text": f"[Selection from {ide_selection.get('file', 'editor')}]\n```\n{ide_selection['text']}\n```",
            }
        )

    cwd = getattr(context, "cwd", None) or ""
    processed_text = _process_mentions(text, mentions, cwd=cwd)
    if processed_text.strip():
        content_blocks.append(
            {
                "type": "text",
                "text": processed_text,
            }
        )

    # Process pasted contents
    if pasted_contents:
        for content in pasted_contents:
            if content.get("type") == "image":
                content_blocks.append(
                    {
                        "type": "image",
                        "source": content.get("source"),
                    }
                )
            elif content.get("type") == "text":
                content_blocks.append(
                    {
                        "type": "text",
                        "text": content.get("text", ""),
                    }
                )

    if content_blocks:
        result["messages"] = [
            {
                "type": "user",
                "id": str(uuid.uuid4()),
                "content": content_blocks,
            }
        ]

    return result


def extract_mentions(text: str) -> list[MentionDict]:
    """Extract @ mentions from text.

    Supports:
    - @filename.ext
    - @path/to/file
    - @agent-name
    - @tool:toolname
    """
    mentions = []

    # Pattern for @ mentions
    pattern = r"@([\w./-]+(?:\:\w+)?)"

    for match in re.finditer(pattern, text):
        mention = match.group(1)
        start = match.start()
        end = match.end()

        mention_type = "file"
        if mention.startswith("tool:"):
            mention_type = "tool"
            mention = mention[5:]
        elif "/" not in mention and "." not in mention:
            # Could be an agent name
            mention_type = "agent"

        mentions.append(
            {
                "type": mention_type,
                "value": mention,
                "start": start,
                "end": end,
            }
        )

    return mentions


def parse_input_blocks(text: str) -> list[TextBlock]:
    """Parse input text into blocks.

    Identifies:
    - Regular text
    - Code blocks (```...```)
    - Inline code (`...`)
    - Mentions (@...)
    """
    blocks = []
    current_pos = 0

    # Pattern for code blocks
    code_block_pattern = re.compile(r"```(\w*)\n?(.*?)```", re.DOTALL)

    for match in code_block_pattern.finditer(text):
        # Add text before code block
        if match.start() > current_pos:
            text_content = text[current_pos : match.start()]
            if text_content.strip():
                blocks.append(
                    TextBlock(
                        type="text",
                        content=text_content,
                    )
                )

        # Add code block
        language = match.group(1) or "text"
        code_content = match.group(2)
        blocks.append(
            TextBlock(
                type="code",
                content=code_content,
                metadata={"language": language},
            )
        )

        current_pos = match.end()

    # Add remaining text
    if current_pos < len(text):
        remaining = text[current_pos:]
        if remaining.strip():
            blocks.append(
                TextBlock(
                    type="text",
                    content=remaining,
                )
            )

    # If no blocks found, treat whole text as single block
    if not blocks and text.strip():
        blocks.append(
            TextBlock(
                type="text",
                content=text,
            )
        )

    return blocks


def _process_mentions(text: str, mentions: list[dict[str, Any]], *, cwd: str = "") -> str:
    """Expand @file mentions with file contents; annotate @agent mentions."""
    if not mentions:
        return text

    out: list[str] = []
    last_end = 0
    for m in sorted(mentions, key=lambda x: x["start"]):
        start, end = m["start"], m["end"]
        out.append(text[last_end:start])
        label = text[start:end]
        out.append(label)

        if m["type"] == "file":
            body = _resolve_file_mention(m["value"], cwd)
            if body is not None:
                max_chars = 120_000
                if len(body) > max_chars:
                    body = body[:max_chars] + "\n… [truncated]"
                out.append(f"\n```\n{body}\n```\n")
        elif m["type"] == "agent":
            out.append(f"\n[Note: agent context for `{m['value']}` is not loaded automatically.]\n")
        elif m["type"] == "tool":
            out.append(f"\n[Note: tool `{m['value']}` mentioned.]\n")

        last_end = end

    out.append(text[last_end:])
    return "".join(out)


def _resolve_file_mention(mention: str, cwd: str) -> str | None:
    """Resolve a file mention to actual file content.

    Returns None if file doesn't exist.
    """
    from pathlib import Path

    # Try relative to cwd
    path = Path(cwd) / mention
    if path.exists() and path.is_file():
        try:
            return path.read_text()
        except Exception:
            pass

    # Try absolute
    path = Path(mention)
    if path.is_absolute() and path.exists() and path.is_file():
        try:
            return path.read_text()
        except Exception:
            pass

    return None
