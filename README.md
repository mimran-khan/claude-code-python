<div align="center">

**📦 [Original TypeScript Source](https://github.com/mimran-khan/claude-code-source)** - The leaked codebase (512k+ lines, 1,900+ files)

---

<img src="https://img.shields.io/badge/🐍_Python-Claude_Code-3776AB?style=for-the-badge&labelColor=1a1a2e" alt="Claude Code Python" width="280">

# Claude Code Python

**Complete Python Port of Anthropic's Agentic Coding Assistant**

*Migrated from the leaked TypeScript source*

[![Stars](https://img.shields.io/github/stars/mimran-khan/claude-code-python?style=flat-square&logo=github&label=Stars&color=yellow)](https://github.com/mimran-khan/claude-code-python/stargazers)
[![Forks](https://img.shields.io/github/forks/mimran-khan/claude-code-python?style=flat-square&logo=github&label=Forks&color=blue)](https://github.com/mimran-khan/claude-code-python/network/members)
[![Watchers](https://img.shields.io/github/watchers/mimran-khan/claude-code-python?style=flat-square&logo=github&label=Watchers&color=green)](https://github.com/mimran-khan/claude-code-python/watchers)
[![Views](https://komarev.com/ghpvc/?username=mimran-khan-claude-code-python&label=Views&color=blueviolet&style=flat-square)](https://github.com/mimran-khan/claude-code-python)

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/Tests-925_passing-4CAF50?style=flat-square&logo=pytest)](./tests/)
[![Lines](https://img.shields.io/badge/Lines-149k+-blue?style=flat-square)](./src/)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](./LICENSE)

[Installation](#installation) · [Usage](#usage) · [Architecture](#architecture) · [Documentation](#documentation)

</div>

---

## ⚠️ DISCLAIMER

> **📚 EDUCATIONAL & RESEARCH PURPOSES ONLY** - This is a Python port of code accidentally leaked by Anthropic. Original code is proprietary and owned by Anthropic.

---

## 🚀 The Migration

| Metric | Value |
|:-------|------:|
| Python modules | **1,805** |
| Lines of code | **149,032** |
| Unit tests | **925** |
| Tools ported | **88** |
| Services | **40+** |
| Commands | **85+** |

✅ Full query engine with tool-use loop · ✅ All 88 agent tools · ✅ Complete service layer · ✅ Working CLI · ✅ Type hints throughout

---

## 📦 Installation

```bash
git clone https://github.com/mimran-khan/claude-code-python.git
cd claude-code-python
python3.11 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
export ANTHROPIC_API_KEY="sk-ant-..."
```

Verify: `claude --version && claude doctor`

---

## 💻 Usage

**CLI:**
```bash
claude                    # Interactive chat
claude -p "Your query"    # One-shot query
claude doctor             # Diagnostics
```

**Python API:**
```python
from claude_code.core.query_engine import QueryEngine, QueryEngineConfig
import asyncio

async def main():
    engine = QueryEngine(QueryEngineConfig(cwd="/path/to/project", tools=[], max_tokens=4096))
    response = await engine.query("What files are in this directory?")
    print(response)

asyncio.run(main())
```

---

## 🏗️ Architecture

```
src/claude_code/
├── core/       # Query engine, tool contracts
├── cli/        # Typer-based CLI
├── tools/      # 88 tool implementations
├── services/   # API, MCP, OAuth, compaction
├── commands/   # Slash commands
├── hooks/      # Event system
└── utils/      # 500+ utility modules
```

---

## 🛠️ Tools

| Category | Tools |
|:---------|:------|
| **File** | Read, Write, Edit, MultiEdit, Glob, Grep, Search |
| **Shell** | Bash, PowerShell, subprocess |
| **Web** | WebFetch, WebSearch |
| **MCP** | Full client, tool discovery, OAuth |
| **Agent** | AgentTool, TaskTool, sub-agents |

---

## 📚 Documentation

[ARCHITECTURE](./docs/ARCHITECTURE.md) · [TOOLS](./docs/TOOLS.md) · [SERVICES](./docs/SERVICES.md) · [API](./docs/API.md) · [CHANGELOG](./CHANGELOG.md)

---

## 🧪 Development

```bash
pytest                              # Run tests
pytest --cov=src/claude_code        # With coverage
ruff check src tests --fix          # Lint
mypy src                            # Type check
```

---

## 🔗 Related

[📦 TypeScript Source](https://github.com/mimran-khan/claude-code-source) · [🌐 Live Analysis](https://mimran-khan.github.io/claude-code-source/)

---

<div align="center">

[![Repo Size](https://img.shields.io/github/repo-size/mimran-khan/claude-code-python?style=flat-square&label=Size)](https://github.com/mimran-khan/claude-code-python)
[![Last Commit](https://img.shields.io/github/last-commit/mimran-khan/claude-code-python?style=flat-square&label=Updated)](https://github.com/mimran-khan/claude-code-python)

**📚 For Educational Purposes Only** · *Not affiliated with Anthropic*

</div>
