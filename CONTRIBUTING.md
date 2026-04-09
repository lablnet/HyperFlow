# Contributing to HyperFlow

First off, thanks for taking the time to contribute!

## How to Contribute

1. **Reporting Bugs**: Use GitHub Issues.
2. **Feature Requests**: Check existing issues before opening a new one.
3. **Pull Requests**:
    - Fork the repo.
    - Create a new branch.
    - Ensure code passes lints (if applicable).
    - Submit the PR!

## Environment Setup

```bash
# Clone the repository
git clone https://github.com/lablnet/HyperFlow.git
cd HyperFlow

# Create a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"
```

## Linting

We use `ruff` for linting and formatting:
```bash
ruff check .
ruff format .
```
