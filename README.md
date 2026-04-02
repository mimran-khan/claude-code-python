<div align="center">

> **📦 Looking for the original TypeScript source?**
> 
> **[👉 Check out claude-code-source](https://github.com/mimran-khan/claude-code-source)** - The leaked TypeScript codebase (512k+ lines, 1,900+ files)

<br>

<img src="https://img.shields.io/badge/🐍_Python-Claude_Code-3776AB?style=for-the-badge&labelColor=1a1a2e" alt="Claude Code Python" width="350">

<br><br>

# Claude Code Python

### Complete Python Port of Anthropic's Agentic Coding Assistant

##### *Migrated from the leaked TypeScript source*

<br>

<a href="https://github.com/mimran-khan/claude-code-python/stargazers">
  <img src="https://img.shields.io/github/stars/mimran-khan/claude-code-python?style=for-the-badge&logo=github&logoColor=white&label=Stars&color=yellow" alt="Stars">
</a>
<a href="https://github.com/mimran-khan/claude-code-python/network/members">
  <img src="https://img.shields.io/github/forks/mimran-khan/claude-code-python?style=for-the-badge&logo=github&logoColor=white&label=Forks&color=blue" alt="Forks">
</a>
<a href="https://github.com/mimran-khan/claude-code-python/watchers">
  <img src="https://img.shields.io/github/watchers/mimran-khan/claude-code-python?style=for-the-badge&logo=github&logoColor=white&label=Watchers&color=green" alt="Watchers">
</a>

<br><br>

<img src="https://komarev.com/ghpvc/?username=mimran-khan-claude-code-python&label=Profile%20Views&color=blueviolet&style=for-the-badge" alt="Profile Views">

<br><br>

[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/Tests-925_passing-4CAF50?style=flat-square&logo=pytest&logoColor=white)](./tests/)
[![Lines](https://img.shields.io/badge/Lines-149k+-blue?style=flat-square)](./src/)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](./LICENSE)

<br>

[Why Python?](#-why-python) · [Installation](#-installation) · [Usage](#-usage) · [Architecture](#-architecture) · [Documentation](#-documentation)

</div>

<br>

---

<br>

## ⚠️ DISCLAIMER

> **📚 EDUCATIONAL & RESEARCH PURPOSES ONLY**
>
> This is a Python port of code that was **accidentally leaked** by Anthropic through their npm package on **March 31, 2026**.
>
> | ❌ DO NOT | ✅ DO |
> |:----------|:------|
> | Use for commercial purposes | Use for learning and research |
> | Create competing products | Study AI coding assistant architecture |
> | Redistribute for profit | Understand agentic tool systems |
>
> **Original code is proprietary and owned by Anthropic.**

<br>

---

<br>

## 🚀 The Migration

This repository is a **complete, line-by-line Python port** of Claude Code's TypeScript backend.

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

The original Claude Code is locked to Node.js. This Python port enables:

<table>
<tr>
<td align="center" width="25%">
<br>
<img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/python/python-original.svg" width="48">
<br><br>
<b>Python Developers</b>
<br>
<sub>Native integration with your codebase</sub>
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
<sub>Embed in FastAPI, Django, Flask</sub>
<br><br>
</td>
<td align="center" width="25%">
<br>
<img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/pytorch/pytorch-original.svg" width="48">
<br><br>
<b>ML Engineers</b>
<br>
<sub>Integrate with training workflows</sub>
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

### Setup

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
    engine = QueryEngine(QueryEngineConfig(
        cwd="/path/to/your/project",
        tools=[],  # Tools are auto-loaded
        max_tokens=4096,
    ))
    
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

## 🔗 Related

- **[📦 Original TypeScript Source](https://github.com/mimran-khan/claude-code-source)** - The leaked codebase
- **[🌐 Live Analysis](https://mimran-khan.github.io/claude-code-source/)** - Interactive website

<br>

---

<br>

## 📜 Legal Notice

This source code is based on **proprietary code owned by Anthropic**. 

This repository exists **strictly for educational and research purposes**.

**All rights reserved by Anthropic.**

<br>

---

<br>

<div align="center">

## 📈 Repository Stats

<br>

<img src="https://img.shields.io/github/repo-size/mimran-khan/claude-code-python?style=for-the-badge&logo=github&label=Repo%20Size&color=orange" alt="Repo Size">
<img src="https://img.shields.io/github/last-commit/mimran-khan/claude-code-python?style=for-the-badge&logo=github&label=Last%20Commit&color=purple" alt="Last Commit">
<img src="https://img.shields.io/github/commit-activity/m/mimran-khan/claude-code-python?style=for-the-badge&logo=github&label=Commits/Month&color=green" alt="Commit Activity">

<br><br>

**[⭐ Star](https://github.com/mimran-khan/claude-code-python) · [🍴 Fork](https://github.com/mimran-khan/claude-code-python/fork) · [🐛 Report Issue](https://github.com/mimran-khan/claude-code-python/issues) · [💬 Discussions](https://github.com/mimran-khan/claude-code-python/discussions)**

<br>

---

<br>

**📚 For Educational Purposes Only**

<br>

*Not affiliated with Anthropic*

</div>
