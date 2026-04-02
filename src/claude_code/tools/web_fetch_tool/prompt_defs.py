"""
WebFetch tool name, description, and secondary-model prompt helper.

Migrated from: tools/WebFetchTool/prompt.ts
"""

from __future__ import annotations

WEB_FETCH_TOOL_NAME = "WebFetch"

DESCRIPTION = """
- Fetches content from a specified URL and processes it using an AI model
- Takes a URL and a prompt as input
- Fetches the URL content, converts HTML to markdown
- Processes the content with the prompt using a small, fast model
- Returns the model's response about the content
- Use this tool when you need to retrieve and analyze web content

Usage notes:
  - IMPORTANT: If an MCP-provided web fetch tool is available, prefer using that tool instead of this one, as it may have fewer restrictions.
  - The URL must be a fully-formed valid URL
  - HTTP URLs will be automatically upgraded to HTTPS
  - The prompt should describe what information you want to extract from the page
  - This tool is read-only and does not modify any files
  - Results may be summarized if the content is very large
  - Includes a self-cleaning 15-minute cache for faster responses when repeatedly accessing the same URL
  - When a URL redirects to a different host, the tool will inform you and provide the redirect URL in a special format. You should then make a new WebFetch request with the redirect URL to fetch the content.
  - For GitHub URLs, prefer using the gh CLI via Bash instead (e.g., gh pr view, gh issue view, gh api).
""".strip()


def make_secondary_model_prompt(
    markdown_content: str,
    prompt: str,
    is_preapproved_domain: bool,
) -> str:
    """Build the user message for the small model that summarizes fetched page content."""
    if is_preapproved_domain:
        guidelines = (
            "Provide a concise response based on the content above. Include relevant details, "
            "code examples, and documentation excerpts as needed."
        )
    else:
        guidelines = """Provide a concise response based only on the content above. In your response:
 - Enforce a strict 125-character maximum for quotes from any source document. Open Source Software is ok as long as we respect the license.
 - Use quotation marks for exact language from articles; any language outside of the quotation should never be word-for-word the same.
 - You are not a lawyer and never comment on the legality of your own prompts and responses.
 - Never produce or reproduce exact song lyrics."""

    return f"""
Web page content:
---
{markdown_content}
---

{prompt}

{guidelines}
"""
