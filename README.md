<div align="center">

<img src="https://img.shields.io/badge/🐍-Claude_Code_Python-blue?style=for-the-badge&labelColor=1a1a2e" alt="Claude Code Python" width="400">

<br><br>

# Claude Code Python

### A Complete Python Implementation of Anthropic's Agentic Coding Assistant

<br>

[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/Tests-925_passing-4CAF50?style=flat-square&logo=pytest&logoColor=white)](./tests/)
[![Coverage](https://img.shields.io/badge/Coverage-34%25-yellow?style=flat-square)](./tests/)
[![Code Style](https://img.shields.io/badge/Code_Style-Ruff-D7FF64?style=flat-square&logo=ruff&logoColor=black)](https://docs.astral.sh/ruff/)
[![Type Checked](https://img.shields.io/badge/Type_Checked-mypy-blue?style=flat-square)](http://mypy-lang.org/)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](./LICENSE)

<br>

[Why Python?](#-why-python) · [Installation](#-installation) · [Usage](#-usage) · [Architecture](#-architecture) · [Documentation](#-documentation)

</div>

<br>

---

<br>

## 🚀 The Migration

This repository contains a **complete, line-by-line Python port** of Claude Code—Anthropic's powerful agentic coding CLI. What started as a TypeScript/Node.js codebase has been systematically transformed into idiomatic, production-ready Python.

<br>

<table>
<tr>
<td width="50%">

### 📊 By the Numbers

| Metric | Value |
|:-------|------:|
| Python modules | **1,805** |
| Lines of code | **149,032** |
| Unit tests | **925** |
| Tools ported | **88** |
| Services ported | **40+** |
| Commands ported | **85+** |

</td>
<td width="50%">

### ⚡ What's Included

- ✅ Full query engine with tool-use loop
- ✅ All 88 agent tools (file, shell, web, MCP)
- ✅ Complete service layer (API, OAuth, MCP)
- ✅ Working CLI with interactive mode
- ✅ Comprehensive test suite
- ✅ Type hints throughout

</td>
</tr>
</table>

<br>

---

<br>

## 🎯 Why Python?

Claude Code is an exceptional piece of engineering, but it's locked to the Node.js ecosystem. This port unlocks it for:

<br>

<table>
<tr>
<td align="center" width="25%">
<br>
<img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/python/python-original.svg" width="48">
<br><br>
<b>Python Developers</b>
<br>
<sub>Native integration with your existing Python codebase</sub>
<br><br>
</td>
<td align="center" width="25%">
<br>
<img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/jupyter/jupyter-original.svg" width="48">
<br><br>
<b>Data Scientists</b>
<br>
<sub>Use in notebooks and ML pipelines</sub>
<br><br>
</td>
<td align="center" width="25%">
<br>
<img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/fastapi/fastapi-original.svg" width="48">
<br><br>
<b>Backend Teams</b>
<br>
<sub>Embed in FastAPI, Django, Flask apps</sub>
<br><br>
</td>
<td align="center" width="25%">
<br>
<img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/pytorch/pytorch-original.svg" width="48">
<br><br>
<b>ML Engineers</b>
<br>
<sub>Direct integration with training workflows</sub>
<br><br>
</td>
</tr>
</table>

<br>

---

<br>

## 📦 Installation

### Requirements

- Python 3.11 or higher
- An Anthropic API key

### Quick Install

```bash
# Clone the repository
git clone https://github.com/mimran-khan/claude-code-python.git
cd claude-code-python

# Create and activate virtual environment
python3.11 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install the package
pip install -e ".[dev]"

# Set your API key
export ANTHROPIC_API_KEY="sk-ant-..."
```

### Verify Installation

```bash
claude --version
claude doctor
```

<br>

---

<br>

## 💻 Usage

### Command Line

```bash
# Start interactive chat
claude

# One-shot query (print mode)
claude -p "Explain what this codebase does"

# With a specific model
claude -m claude-sonnet-4-20250514 -p "Write a Python hello world"

# Run diagnostics
claude doctor

# View/edit configuration
claude config
```

### Python API

```python
import asyncio
from claude_code.core.query_engine import QueryEngine, QueryEngineConfig

async def main():
    # Initialize the engine
    engine = QueryEngine(QueryEngineConfig(
        cwd="/path/to/your/project",
        tools=[],  # Tools are auto-loaded
        max_tokens=4096,
    ))
    
    # Send a query
    response = await engine.query("What files are in this directory?")
    print(response)

asyncio.run(main())
```

### Streaming Responses

```python
async def stream_example():
    engine = QueryEngine(config)
    
    async for chunk in engine.stream("Explain this codebase"):
        print(chunk, end="", flush=True)
```

<br>

---

<br>

## 🛠️ Tools

All 88 tools from the original Claude Code have been ported:

| Category | Tools |
|:---------|:------|
| **File Operations** | `Read`, `Write`, `Edit`, `MultiEdit`, `Glob`, `Grep`, `Search` |
| **Shell Execution** | `Bash`, `PowerShell`, subprocess with timeout/abort |
| **Web Access** | `WebFetch`, `WebSearch` |
| **MCP Protocol** | Full client implementation, tool discovery, OAuth |
| **Agent System** | `AgentTool`, `TaskTool`, sub-agent spawning |
| **Notebooks** | Jupyter notebook reading and editing |
| **Memory** | Todo lists, task management, session state |
| **Planning** | Plan mode, thinking tools, mode switching |

<br>

---

<br>

## 🏗️ Architecture

```
src/claude_code/
├── core/                 # Query engine, tool contracts, context
├── engine/               # High-level SDK interface
├── cli/                  # Typer-based command line interface
├── tools/                # 88 tool implementations
│   ├── bash_tool/
│   ├── file_read_tool/
│   ├── grep_tool/
│   ├── mcp_tool/
│   └── ...
├── services/             # External integrations
│   ├── api/              # Anthropic API client
│   ├── mcp/              # Model Context Protocol
│   ├── compact/          # Context compaction
│   ├── oauth/            # Authentication
│   └── ...
├── hooks/                # Event system
├── commands/             # Slash commands (/commit, /review, etc.)
├── bridge/               # Remote session management
└── utils/                # Shared utilities (500+ modules)
```

### Request Flow

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│  User Input │────▶│ Query Engine │────▶│  Anthropic API  │
└─────────────┘     └──────────────┘     └─────────────────┘
                           │                      │
                           │                      ▼
                           │              ┌───────────────┐
                           │              │ Tool Use?     │
                           │              └───────────────┘
                           │                 Yes │    │ No
                           │                     ▼    │
                           │              ┌──────────┐│
                           │◀─────────────│ Execute  ││
                           │              │   Tool   ││
                           │              └──────────┘│
                           │                          ▼
                           │                   ┌──────────┐
                           └──────────────────▶│ Response │
                                               └──────────┘
```

<br>

---

<br>

## 📚 Documentation

| Document | Description |
|:---------|:------------|
| [ARCHITECTURE.md](./docs/ARCHITECTURE.md) | System design, component relationships |
| [TOOLS.md](./docs/TOOLS.md) | Complete tool reference with examples |
| [SERVICES.md](./docs/SERVICES.md) | Service layer documentation |
| [API.md](./docs/API.md) | Python API reference |
| [DATA_FLOW.md](./docs/DATA_FLOW.md) | Request/response flow diagrams |
| [PACKAGES.md](./docs/PACKAGES.md) | Package structure breakdown |
| [CHANGELOG.md](./CHANGELOG.md) | Version history |

<br>

---

<br>

## 🧪 Development

### Running Tests

```bash
# All tests
pytest

# With coverage report
pytest --cov=src/claude_code --cov-report=html

# Specific test file
pytest tests/test_core.py -v

# Skip slow integration tests
pytest -m "not integration"
```

### Code Quality

```bash
# Lint and format
ruff check src tests --fix
ruff format src tests

# Type checking
mypy src

# All checks
ruff check . && ruff format --check . && mypy src && pytest
```

### Project Structure

```bash
claude-code-python/
├── src/claude_code/     # Source code (1,805 modules)
├── tests/               # Test suite (89 files, 925 tests)
├── docs/                # Documentation
├── examples/            # Usage examples
├── pyproject.toml       # Package configuration
└── uv.lock              # Locked dependencies
```

<br>

---

<br>

## ⚙️ Configuration

### Environment Variables

| Variable | Required | Description |
|:---------|:--------:|:------------|
| `ANTHROPIC_API_KEY` | ✅ | Your Anthropic API key |
| `CLAUDE_CODE_MODEL` | | Default model (e.g., `claude-sonnet-4-20250514`) |
| `CLAUDE_CODE_THINKING` | | Thinking mode: `true`, `false`, `adaptive` |
| `CLAUDE_CONFIG_DIR` | | Custom config directory path |

### Config File

Located at `~/.claude/config.json`:

```json
{
  "model": "claude-sonnet-4-20250514",
  "thinking": "adaptive",
  "permissions": {
    "allow_shell": true,
    "allow_web": true
  }
}
```

<br>

---

<br>

## 🤝 Contributing

Contributions are welcome! Please see [contributing.md](./docs/contributing.md) for guidelines.

```bash
# Setup dev environment
git clone https://github.com/mimran-khan/claude-code-python.git
cd claude-code-python
pip install -e ".[dev]"

# Make changes, then run checks
ruff check src tests --fix
ruff format src tests
mypy src
pytest
```

<br>

---

<br>

## 📄 License

This project is licensed under the MIT License. See [LICENSE](./LICENSE) for details.

<br>

---

<br>

## 🙏 Acknowledgments

This is a community-driven Python port of Claude Code. It is **not** an official Anthropic product.

- Thanks to Anthropic for creating Claude Code
- Thanks to the Python community for the excellent tooling ecosystem

<br>

---

<br>

<div align="center">

**[Report Issue](https://github.com/mimran-khan/claude-code-python/issues) · [Request Feature](https://github.com/mimran-khan/claude-code-python/issues) · [Discussions](https://github.com/mimran-khan/claude-code-python/discussions)**

<br>

Made with 🐍 for the Python community

</div>
