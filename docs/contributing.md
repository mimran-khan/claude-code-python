# Contributing

Thank you for helping improve the Python Claude Code migration. This guide covers environment setup, quality gates, and patch expectations.

## Prerequisites

- Python **3.11+**
- `git`
- Recommended: virtual environment (`venv`) per clone

## Set up the dev environment

```bash
cd claude-code-python
python3.11 -m venv .venv
source .venv/bin/activate   # or Windows equivalent
pip install -e ".[dev]"
```

Set **`ANTHROPIC_API_KEY`** when exercising API-backed paths locally.

## Code layout

- **`src/claude_code/`** — all application code (installed package)
- **`tests/`** — pytest tests; `pythonpath = ["src"]` is configured in `pyproject.toml`

When adding features, prefer matching the existing **TypeScript parity** style: small modules, explicit types, and a short **“Migrated from:”** note in new files when porting.

## Linting and formatting (Ruff)

```bash
ruff check src tests
ruff format src tests
```

Settings live in `[tool.ruff]` and `[tool.ruff.lint]` in `pyproject.toml` (line length 100, Python 3.11 target). Some paths have per-file ignores (e.g. computer-use stubs).

## Type checking (mypy)

```bash
mypy src
```

The project uses **`strict = true`**. Avoid unnecessary `# type: ignore`; fix types at the source when possible.

## Tests (pytest)

```bash
pytest
pytest -q --tb=short
pytest -m "not integration"   # skip integration-marked tests
pytest --cov=claude_code --cov-report=term-missing
```

- **`asyncio_mode = auto`** — async tests do not need special markers unless you need sync behavior.
- Use the **`integration`** marker for tests that touch the real filesystem, git, or long-running subprocesses.

## Commit and PR hygiene

- Keep changes **focused** (one logical concern per PR when possible).
- **Conventional commits** are welcome, e.g. `feat:`, `fix:`, `docs:`, `test:`, `refactor:`.
- Do not commit **secrets** (API keys, tokens); use environment variables.
- Update **user-facing docs** (`README.md`, `docs/`) when behavior or CLI flags change.

## Documentation

- **README** — install, CLI, quick usage, testing.
- **`docs/ARCHITECTURE.md`** — system map; update when you add major packages or change the query flow.
- **`docs/TOOLS.md`** / **`docs/SERVICES.md`** — registries; update when adding prominent tools or services.

## Definition of done (checklist)

Before opening a PR:

- [ ] `ruff check` and `ruff format` clean (or equivalent project standard)
- [ ] `mypy src` passes
- [ ] `pytest` passes (or explain skipped integration tests)
- [ ] New behavior documented if user-visible (README or `docs/`)

## Getting help

- Inspect **existing tests** for examples of how to mock API and MCP boundaries.
- Read **[ARCHITECTURE.md](ARCHITECTURE.md)** for where CLI, engine, tools, and services meet.
