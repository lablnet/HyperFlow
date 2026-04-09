# HyperFlow (Python)

A self-improving agent framework built on LangChain and LangGraph. Python port of [HyperAgents](../README.md) (TypeScript).

## Overview

HyperFlow runs an **evolutionary self-improvement loop**: a **MetaAgent** edits the **TaskAgent** (and optionally prompt files) using **bash + editor** tools; each variant is **evaluated** on domain tasks; results and patches go into a **JSONL archive**; **parent selection** picks the next lineage to mutate.

Supports **local or Docker** execution, multiple **LLM providers** (OpenAI, Anthropic, Google Gemini, Ollama), and pluggable **domains** and **evaluators** (static, LLM judge, human feedback).

## Installation

```bash
# From the python/ directory
pip install -e .

# Or install dependencies directly
pip install -r requirements.txt
```

### Requirements

- Python 3.11+
- At least one LLM provider API key (e.g. `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`)

## Quick Start

```bash
# Set your API key
export OPENAI_API_KEY="sk-..."

# Run the bash example (single eval)
cd examples/bash
python run.py

# Run with evolutionary loop
python run.py evolve
```

## Project Structure

```
hyperflow/
  __init__.py           # Public API re-exports
  agent/
    base_agent.py       # Abstract AgentSystem base class
    llm.py              # Multi-provider LLM factory
    llm_with_tools.py   # LangGraph ReAct chat loop
    meta_agent.py       # MetaAgent (mutation operator)
    task_agent.py       # TaskAgent (task solver)
    tool_registry.py    # Tool registration
  core/
    ensemble.py         # Best-of-archive ensemble
    generate_loop.py    # Main evolutionary loop
    select_parent.py    # Parent selection strategies
  domains/
    base.py             # Domain/DomainTask/EvalResult interfaces
    evaluators.py       # Static, LLM judge, human evaluators
    harness.py          # Evaluation harness
    report.py           # Report generation
  prompts/
    llm_judge.py        # LLM judge prompt template
    meta_agent.py       # MetaAgent prompt template
    task_agent.py       # TaskAgent prompt template
  tools/
    __init__.py         # get_framework_tools()
    bash.py             # Bash shell tool
    editor.py           # File editor tool
  utils/
    archive.py          # JSONL archive CRUD
    common.py           # JSON extraction, file helpers
    constants.py        # Shared constants
    docker.py           # Docker container management
    executor.py         # Local/Docker execution
    git.py              # Git operations
examples/
  bash/                 # Bash command generation
  calculator/           # Buggy tool fix demo
  factcheck/            # True/false classification
  git_evolution/        # Git-based evolution with patches
  paper_review/         # Paper accept/reject prediction
  scoring/              # Math grading self-improvement
```

## Supported Models

```python
from hyperflow import MODELS

# Available model presets
MODELS["OPENAI_GPT4O"]       # "openai/gpt-4o"
MODELS["OPENAI_GPT4O_MINI"]  # "openai/gpt-4o-mini"
MODELS["OPENAI_O3"]          # "openai/o3"
MODELS["OPENAI_O4_MINI"]     # "openai/o4-mini"
MODELS["CLAUDE_SONNET"]      # "anthropic/claude-sonnet-4-5-20250929"
MODELS["GEMINI_PRO"]         # "gemini/gemini-2.5-pro"
MODELS["OLLAMA_LLAMA3"]      # "ollama/llama3"
```

Or use any `"provider/model-name"` string.

## Environment Variables

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | OpenAI API key |
| `ANTHROPIC_API_KEY` | Anthropic API key |
| `GOOGLE_API_KEY` | Google Gemini API key |
| `OLLAMA_BASE_URL` | Ollama server URL (default: `http://localhost:11434`) |
| `HYPERFLOW_MODEL` | Default model for examples (e.g. `openai/gpt-4o`) |

## Examples

### Single Evaluation

```bash
cd examples/bash && python run.py
cd examples/factcheck && python run.py
cd examples/paper_review && python run.py
```

### Evolutionary Self-Improvement

```bash
cd examples/bash && python run.py evolve
cd examples/factcheck && python run.py evolve
cd examples/scoring && python run.py
cd examples/calculator && python run.py
cd examples/git_evolution && python run.py
```

### Git-Based Evolution (with patches)

```bash
cd examples/git_evolution && python run.py        # 2 generations
cd examples/git_evolution && python run.py 5      # 5 generations
cd examples/git_evolution && python run.py --reset # start over
```

## License

MIT
