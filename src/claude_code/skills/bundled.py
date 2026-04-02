"""
Bundled skills.

Built-in skills shipped with Claude Code.

Migrated from: skills/bundledSkills.ts
"""

from __future__ import annotations

from .loader import Skill, SkillFrontmatter

# Bundled skills definitions
BUNDLED_SKILLS: list[Skill] = [
    Skill(
        name="debug",
        path="bundled:debug",
        content="""When debugging an issue, follow these steps:

1. **Reproduce the issue** - Understand the exact steps to reproduce
2. **Read relevant code** - Use file read tools to examine the code
3. **Add diagnostic output** - Add logging/print statements if needed
4. **Form a hypothesis** - Based on the code and error, hypothesize the cause
5. **Test the hypothesis** - Make minimal changes to verify
6. **Fix the root cause** - Implement the proper fix
7. **Verify the fix** - Ensure the issue is resolved and no regressions

Always explain your reasoning at each step.""",
        source="bundled",
        frontmatter=SkillFrontmatter(
            description="Systematic debugging workflow",
        ),
    ),
    Skill(
        name="refactor",
        path="bundled:refactor",
        content="""When refactoring code, follow these principles:

1. **Understand the current code** - Read and understand before changing
2. **Identify code smells** - Look for duplication, long methods, etc.
3. **Plan the refactoring** - Decide on the approach
4. **Make incremental changes** - Small, safe changes one at a time
5. **Verify after each change** - Ensure behavior is preserved
6. **Document significant changes** - Update comments/docs if needed

Common refactoring patterns:
- Extract method/function
- Rename for clarity
- Remove duplication
- Simplify conditionals
- Split large files""",
        source="bundled",
        frontmatter=SkillFrontmatter(
            description="Code refactoring best practices",
        ),
    ),
    Skill(
        name="test",
        path="bundled:test",
        content="""When writing tests, follow these guidelines:

1. **Test structure** - Arrange, Act, Assert pattern
2. **Test naming** - Clear names describing the scenario
3. **Test isolation** - Each test should be independent
4. **Edge cases** - Test boundaries and error conditions
5. **Mocking** - Mock external dependencies appropriately

For each feature, consider:
- Happy path tests
- Error handling tests
- Edge case tests
- Integration tests where appropriate""",
        source="bundled",
        frontmatter=SkillFrontmatter(
            description="Test writing guidelines",
        ),
    ),
    Skill(
        name="review",
        path="bundled:review",
        content="""When reviewing code changes:

1. **Understand the context** - Read PR description and linked issues
2. **Check correctness** - Does the code do what it claims?
3. **Check edge cases** - Are error conditions handled?
4. **Check style** - Does it follow project conventions?
5. **Check tests** - Are changes adequately tested?
6. **Check security** - Any potential security issues?
7. **Provide constructive feedback** - Be specific and helpful""",
        source="bundled",
        frontmatter=SkillFrontmatter(
            description="Code review checklist",
        ),
    ),
]


def get_bundled_skill(name: str) -> Skill | None:
    """
    Get a bundled skill by name.

    Args:
        name: Skill name

    Returns:
        Skill or None
    """
    for skill in BUNDLED_SKILLS:
        if skill.name == name:
            return skill
    return None


def is_bundled_skill(name: str) -> bool:
    """Check if a skill is bundled."""
    return get_bundled_skill(name) is not None
