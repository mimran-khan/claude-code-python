"""
Magic Docs prompts.

Migrated from: services/MagicDocs/prompts.ts
"""


def build_magic_docs_update_prompt(
    file_path: str,
    title: str,
    current_content: str,
    conversation_context: str,
    instructions: str | None = None,
) -> str:
    """Build the prompt for updating a magic doc.

    Args:
        file_path: Path to the magic doc file
        title: Title from the magic doc header
        current_content: Current content of the file
        conversation_context: Context from the conversation
        instructions: Optional instructions from the header

    Returns:
        Prompt for the agent to update the document
    """
    instruction_text = ""
    if instructions:
        instruction_text = f"""
The document has specific instructions: {instructions}
Follow these instructions when updating the document.
"""

    return f"""You are updating a Magic Doc titled "{title}" at {file_path}.

Magic Docs are automatically maintained documentation files that evolve with the conversation.
Your task is to update this document with relevant new learnings from the recent conversation.

{instruction_text}

Current document content:
<current_content>
{current_content}
</current_content>

Conversation context:
<conversation>
{conversation_context}
</conversation>

Instructions:
1. Review the current document and the conversation context
2. Identify any new information, patterns, decisions, or learnings from the conversation
3. Update the document to incorporate these learnings
4. Maintain the document's structure and style
5. Keep the MAGIC DOC header intact
6. Be concise but comprehensive
7. Only add truly relevant information - don't add noise

Use the file edit tool to update the document. If there are no relevant updates to make,
respond that no updates are needed."""


def build_magic_docs_summary_prompt(
    documents: list,
) -> str:
    """Build a prompt for summarizing multiple magic docs.

    Args:
        documents: List of magic doc info dicts

    Returns:
        Summary prompt
    """
    doc_list = "\n".join(f"- {doc.get('path', 'unknown')}: {doc.get('title', 'Untitled')}" for doc in documents)

    return f"""The following Magic Docs are being tracked in this session:

{doc_list}

These documents will be automatically updated as the conversation progresses
to capture relevant learnings and decisions."""
