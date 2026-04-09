# Installation

## Requirements

- **Python 3.11+**
- At least one LLM provider API key (e.g., `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, or `GOOGLE_API_KEY`).
- Docker (optional, but recommended if using `DockerExecutor` for safe agent modifications).

## Standard Installation

Install the package directly from PyPI:

```bash
pip install hyperflow-ai
```

## Install from Source

For development and contributing, install from the source repository:

```bash
git clone https://github.com/lablnet/HyperFlow.git
cd HyperFlow
python3 -m venv .venv
source .venv/bin/activate

pip install -e ".[dev]"
```

## Environment Variables

HyperFlow relies on `.env` files to configure your workspace. Create an `.env` file in your root path:

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | OpenAI API key |
| `ANTHROPIC_API_KEY` | Anthropic API key |
| `GOOGLE_API_KEY` | Google Gemini API key |
| `OLLAMA_BASE_URL` | Ollama server URL (default: `http://localhost:11434`) |
| `HYPERFLOW_MODEL` | Default model for examples (e.g. `openai/gpt-4o`) |
