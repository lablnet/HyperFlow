# Examples

HyperFlow comes with multiple real-world examples showing standard configurations, local improvement loops, or evolutionary setups.

You can run single evaluations to test if an agent behaves well out-of-the-box, or you can invoke evolutionary loops so the agent writes patches to its own logic!

## Example Domains

- **Bash**: Generates terminal commands.
- **Scoring**: Grade student math answers (accept/reject).
- **Calculator**: Solve math problems using a tool.
- **Fact-check**: Classify statements as true/false.
- **Paper Review**: Predict accept/reject for research paper abstracts.
- **Git Evolution**: A comprehensive standard flow utilizing patches across an isolated git structure branch.

## Running the Examples

### Evaluate Single Run

Execute `run.py` to evaluate the current solver logic strictly once.

```bash
cd examples/bash && python run.py
cd examples/factcheck && python run.py
cd examples/paper_review && python run.py
```

### Run Evolutionary Self-Improvement

Execute `run.py evolve` (or via specific script parameters depending on the example) to trigger the evolutionary loop.

```bash
cd examples/bash && python run.py evolve
cd examples/factcheck && python run.py evolve
cd examples/scoring && python run.py
cd examples/calculator && python run.py
cd examples/git_evolution && python run.py
```

For the git-based evolution:
```bash
cd examples/git_evolution && python run.py        # 2 generations
cd examples/git_evolution && python run.py 5      # 5 generations
cd examples/git_evolution && python run.py --reset # Start over
```
