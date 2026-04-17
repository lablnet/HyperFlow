# Advanced concepts and architecture

For diagrams of the loop, harness, and archive, see [Basic concepts](./basic-concepts.md).

## Parent selection strategies

`select_parent` drives which generation is passed into the MetaAgent. Choosing the absolute best generation every time is actually flawed due to local maximums. HyperFlow provides five algorithms via `select_parent.py`:

- **random**: Pick any valid generation with equal probability. Max exploration.
- **latest**: Always pick the most recently created valid generation. Linear progression.
- **best**: Always pick the highest-scoring generation. Max exploitation.
- **score_prop**: Weighted random: higher scores get higher probability.
- **score_child_prop (default)**: Score-weighted + child penalty. Encourages under-visited branches and exploring the global maximum.

## Domains and Evaluation

A **Domain** defines what tasks the agent is evaluated on.
- **Evaluators**: The grading strategy (`evaluators.py`). You can use `static_evaluator` (exact string match), `llm_judge_evaluator` (using LLMs for subjective questions), or `human_feedback_evaluator`.
- **Harness**: The generic evaluation runner (`harness.py`). It formats the domain input, requests a forward pass on the `TaskAgent`, and evaluates it against the task context.

## Architectures

### Execution Modes
The environment is managed by `Executor` abstractions (`executor.py`):
1. **LocalExecutor**: Copies the repository to a localized temp directory. Faster, but has no sandboxing.
2. **DockerExecutor**: Creates a temporary Docker volume and sandboxes the process via Dockerode API (`docker.py`). Excellent for preventing arbitrary code execution escapes since the MetaAgent patches source code itself.

### Self-Referential Improvement
A core concept from the HyperAgents paper is **self-referential self-improvement** — the MetaAgent can modify its own instructions to become a better improver.

We achieve this with editable prompt files (using `prompts_dir`):
- `meta_agent.txt`
- `task_agent.txt`

If configured, the MetaAgent edits the very `.txt` files containing its internal constraints. Thus, the improver improves itself.

### Early Termination
The loop contains intelligent optimizations:
- **Perfect Score Stop**: Reaching 1.0 (100%) gracefully terminates further evaluation routines.
- **Score-Aware MetaAgent**: The MetaAgent adjusts its strictness or focuses solely on edge-cases if the parent agent passes over 90% logic cleanly.
