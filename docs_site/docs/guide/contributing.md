# Contributing

First off, thanks for taking the time to contribute to HyperFlow!

## How to Contribute

1. **Reporting Bugs**: Use GitHub Issues.
2. **Feature Requests**: Check existing issues before opening a new one.
3. **Pull Requests**:
    - Fork the repo.
    - Create a new branch.
    - Ensure code passes lints (if applicable).
    - Submit the PR!

## Environment Setup

To begin hacking on the local components (`GenerateLoopConfig`, the local DOMs and executors):

```bash
# Clone the repository
git clone https://github.com/lablnet/HyperFlow.git
cd HyperFlow

# Create a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies alongside dev additions
pip install -e ".[dev]"
```

## Linting

We use `ruff` to maintain a very clean code base. Formatting must be identical to the internal styles.
Run the linting targets manually before pushing code:

```bash
ruff check .
ruff format .
```
