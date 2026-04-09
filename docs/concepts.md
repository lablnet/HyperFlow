# HyperFlow Concepts

This document explains the core concepts, architecture, and data flow of the HyperFlow framework in detail.

## Table of Contents

- [Overview](#overview)
- [The Two Agents](#the-two-agents)
- [The Evolutionary Loop](#the-evolutionary-loop)
- [The Archive](#the-archive)
- [Parent Selection Strategies](#parent-selection-strategies)
- [Domains and Evaluation](#domains-and-evaluation)
- [Evaluators](#evaluators)
- [The Harness](#the-harness)
- [Predictions vs Scores](#predictions-vs-scores)
- [Executors](#executors)
- [File System Layout](#file-system-layout)
- [JSONL vs JSON](#jsonl-vs-json)
- [Early Termination](#early-termination)
- [Examples Overview](#examples-overview)
- [Glossary](#glossary)

---

## Overview

HyperFlow is a self-improving agent framework. Instead of manually tuning an AI agent, you let another AI agent do it automatically.

The core idea comes from evolutionary computation and Quality-Diversity (QD) algorithms: maintain an **archive** of agent versions, evaluate each one, and use the best-performing versions as starting points for further improvement.

```
┌─────────────────────────────────────────────────┐
│                Evolutionary Loop                 │
│                                                  │
│   ┌──────────┐    ┌───────────┐    ┌──────────┐ │
│   │  Select   │───▶│ MetaAgent │───▶│ Evaluate │ │
│   │  Parent   │    │ (improve) │    │ (score)  │ │
│   └────▲─────┘    └───────────┘    └────┬─────┘ │
│        │                                │        │
│        │         ┌───────────┐          │        │
│        └─────────│  Archive  │◀─────────┘        │
│                  │ (history) │                    │
│                  └───────────┘                    │
└─────────────────────────────────────────────────┘
```

---

## The Two Agents

### TaskAgent — The Worker

The TaskAgent solves domain-specific tasks. It receives a formatted prompt, optionally uses tools, and returns a prediction.

- **Input**: A task description (e.g., "Write a bash command that prints hello world")
- **Output**: A prediction (e.g., `echo "hello world"`)
- **Tools**: Domain-specific, optional (e.g., a calculator tool, bash executor)
- **Code location**: `hyperflow/agent/task_agent.py`

The TaskAgent is intentionally minimal. Its behavior is mostly driven by prompts and tools — which the MetaAgent can modify.

### MetaAgent — The Improver

The MetaAgent's job is to make the TaskAgent better. It reads past evaluation results, identifies failures, and edits source code (prompts, logic, tools) to fix them.

- **Input**: Repo path + eval results path + parent score
- **Output**: Modified source code on disk (patches/diffs)
- **Tools**: `bash` (run shell commands) + `editor` (view/edit files) — built-in
- **Code location**: `hyperflow/agent/meta_agent.py`

The MetaAgent is the "mutation operator" in evolutionary terms. It doesn't solve tasks directly — it rewrites the code that solves tasks.

### How They Work Together

```
MetaAgent runs FIRST:
  "The current score is 70%. Let me read the failures...
   Ah, the prompt doesn't handle edge cases. I'll edit it."
  → Edits prompt.txt, domain.py, etc.

TaskAgent runs SECOND:
  "Write a bash command that prints numbers 1-5"
  → "for i in {1..5}; do echo $i; done"
  → Harness grades it → score 0.85
```

The MetaAgent is the teacher fixing the textbook. The TaskAgent is the student taking the test with the updated textbook.

---

## The Evolutionary Loop

The evolutionary loop (`hyperflow/core/generate_loop.py`) is the heart of the system. It runs multiple generations, each improving on a previous one.

### One Generation Step-by-Step

```
Generation N:
  1. SELECT PARENT     Pick a previous generation from the archive
  2. SETUP EXECUTOR    Create a clean workspace (local dir or Docker container)
  3. APPLY PATCHES     Replay the parent's patch chain to recreate its code state
  4. RUN METAAGENT     MetaAgent reads failures, edits code → produces new patch
  5. RUN TASKAGENT     TaskAgent solves tasks using the improved code
  6. EVALUATE          Harness grades predictions → score
  7. SAVE TO ARCHIVE   Store genId, parentId, patches, scores, metadata
  8. REPEAT            Go to step 1 for the next generation
```

### Configuration

```python
from hyperflow import GenerateLoopConfig

config = GenerateLoopConfig(
    domains=[my_domain],                # What tasks to evaluate on
    meta_agent=meta_agent,              # The MetaAgent instance
    task_agent_factory=lambda t: TaskAgent(AgentOptions(model=model, tools=t)),
    tools=get_framework_tools(),        # bash + editor
    output_dir="./outputs/evolution",   # Where to store everything
    repo_path=".",                      # The codebase to modify
    max_generations=5,                  # How many iterations
    execution_mode="local",             # "local" or "docker"
    parent_selection="score_child_prop",# Which selection strategy
    eval_samples=10,                    # How many tasks per eval
)
```

---

## The Archive

The archive is the central data structure that stores the history of all generations. It serves as a **versioned record of evolutionary improvement** — not a zip file.

The name comes from **MAP-Elites** and **Quality-Diversity (QD) algorithms** in evolutionary computation, where "archive" is the standard term for the collection of solutions.

### Data Structure

```python
from dataclasses import dataclass, field
from typing import Any

@dataclass
class ArchiveEntry:
    gen_id: str | int                       # Unique generation ID
    parent_id: str | int | None             # Which generation this was built from
    patch_files: list[str]                  # All patches in the lineage chain
    scores: dict[str, float]                # Scores per domain
    metadata: dict[str, Any]                # Extra info (model used, etc.)
    valid_parent: bool                      # Can future generations build on this?
    timestamp: str                          # When this was created

@dataclass
class ArchiveData:
    archive: list[str | int]                        # Ordered list of generation IDs
    entries: dict[str, ArchiveEntry]                 # Map of all entries
```

### Storage Format (JSONL)

The archive is stored as a JSONL (JSON Lines) file — one JSON object per line:

```json
{"archive":["initial"],"entries":{"initial":{...}}}
{"archive":["initial",1],"entries":{"initial":{...},"1":{...}}}
{"archive":["initial",1,2],"entries":{"initial":{...},"1":{...},"2":{...}}}
```

Each line is a complete snapshot of the archive state at that point. To get the current state, read the last line. This is append-only — no rewrites needed.

### Archive Functions (`hyperflow/utils/archive.py`)

| Function | Purpose |
|---|---|
| `load_archive(output_dir)` | Read the latest snapshot from `archive.jsonl` |
| `save_archive(output_dir, data)` | Append a new snapshot line |
| `update_archive(output_dir, current, entry)` | Add a new generation and persist |
| `load_gen_metadata(output_dir, gen_id)` | Read `gen_<id>/metadata.json` |
| `save_gen_metadata(output_dir, gen_id, meta)` | Write `gen_<id>/metadata.json` |
| `get_patch_files(output_dir, gen_id)` | Get all patches in a generation's lineage |
| `get_score(domain, output_dir, gen_id, split)` | Read a generation's score from its report |
| `is_starting_node(gen_id)` | Check if gen_id is `"initial"` or `0` |

### The Family Tree

The archive creates a tree structure, not a linear chain. Different generations can branch from different parents:

```
initial (score: 0.0)
  ├── gen1 (score: 0.7)
  │     ├── gen2 (score: 0.65) ─── approach A
  │     │     └── gen4 (score: 0.85)
  │     └── gen3 (score: 0.82) ─── approach B
  └── gen5 (score: 0.3) ─── fresh start from initial
```

Gen 4's parent is gen 2 (not gen 3), even though gen 3 was created first. The `parent_id` field tracks the actual lineage.

---

## Parent Selection Strategies

Parent selection (`hyperflow/core/select_parent.py`) decides which previous generation to use as the starting point for the next one. The strategy is chosen **once** in the config and used for **every generation** throughout the loop.

### Why Not Always Pick the Best?

Because `best` can get stuck at a **local maximum** — a solution that's better than its neighbors but not the best overall.

```
                        ★ Global maximum (0.95)
                       /\
                      /  \
         Local max   /    \
          (0.84)    /      \
           /\      /        \
          /  \    /          \
   ------/    \/              \------
```

If you always pick the highest-scoring parent, you keep refining the same approach and never discover that a different path could reach a higher peak. You'd need to "go downhill" first (pick a lower-scoring parent) to cross the valley and find the global maximum.

### The Five Strategies

**`random`** — Pick any valid generation with equal probability.
- Maximum exploration, zero intelligence about scores.
- Use when: you want to maximize diversity.

**`latest`** — Always pick the most recently created valid generation.
- Simple, linear progression.
- Use when: you want a straightforward chain without branching.

**`best`** — Always pick the highest-scoring generation.
- Maximum exploitation, zero exploration.
- Use when: few generations, just want quick gains.

**`score_prop`** — Weighted random: higher scores get higher probability.
- Mostly picks good parents, occasionally picks weaker ones.
- Balances exploitation and exploration.

**`score_child_prop`** — Score-weighted + child penalty (default).
- Same as `score_prop`, but penalizes parents that already have many children.
- Formula: `weight = (score + 0.01) × 1/(1 + num_children)`
- Encourages exploring under-visited branches.
- Use when: many generations, want to discover diverse improvement paths.

### Example

```
Archive state:
  gen1: score 0.9, 3 children → weight = 0.91 × 1/4 = 0.23
  gen2: score 0.7, 0 children → weight = 0.71 × 1/1 = 0.71  ← likely picked!

Gen2 has a much higher chance despite a lower score,
because gen1 has been explored enough.
```

---

## Domains and Evaluation

A **Domain** defines what tasks the agent is evaluated on. Each domain implements a standard interface (`hyperflow/domains/base.py`):

```python
from abc import ABC, abstractmethod

class Domain(ABC):
    config: DomainConfig

    @abstractmethod
    async def load_tasks(self, subset: str, num_samples: int | None = None) -> list[DomainTask]:
        ...

    @abstractmethod
    async def evaluate(self, prediction: str, task: DomainTask) -> float:
        ...

    @abstractmethod
    def format_input(self, task: DomainTask) -> str:
        ...

    @abstractmethod
    async def report(self, results: list[EvalResult]) -> ReportSummary:
        ...
```

### Built-in Examples

| Domain | Task | Evaluation |
|---|---|---|
| **Bash** | Generate bash commands from descriptions | Execute command, compare output to expected |
| **Scoring** | Grade student math answers (accept/reject) | String match against ground truth |
| **Fact-check** | Classify statements as true/false | String match against ground truth |
| **Calculator** | Solve math problems using a tool | Compare numeric result to expected |
| **Paper Review** | Predict accept/reject for papers | Match against known decisions |

### Creating Your Own Domain

1. Define your tasks in a `tasks.json` file
2. Implement the `Domain` abstract class in a `domain.py` file
3. Create a `run.py` that wires everything together

---

## Evaluators

Evaluators (`hyperflow/domains/evaluators.py`) decide how to score a prediction. Three strategies:

### Static Evaluator
Exact string match after normalization. Free, fast, deterministic.
```python
static_evaluator("42", "42")     # → 1.0
static_evaluator("42", "43")     # → 0.0
static_evaluator(" 42 ", "42")   # → 1.0 (trimmed)
```

### LLM Judge Evaluator
Asks an LLM to score the prediction on a 0-1 scale. Costs money but handles subjective tasks.
```python
await llm_judge_evaluator("Good summary of the article", {
    "description": "Summarize this article",
    "rubric": "Score based on completeness and accuracy",
})  # → 0.85
```

### Human Feedback Evaluator
Converts a user-provided rating to a 0-1 score. Use in production with real user feedback.
```python
human_feedback_evaluator(4 / 5)  # → 0.8
```

---

## The Harness

The harness (`hyperflow/domains/harness.py`) is the generic evaluation runner. It connects a TaskAgent to a Domain's tasks:

```
For each task in the domain:
  1. domain.format_input(task)      → format as prompt
  2. agent.forward(input)           → get prediction
  3. domain.evaluate(prediction)    → get score (0 or 1)

Collect all results → save predictions.json → return average score
```

The harness is used in two contexts:
- **Single eval mode**: called directly in `run.py` to evaluate once
- **Evolutionary loop**: called by `run_generate_loop` after each MetaAgent improvement

---

## Predictions vs Scores

These are two different outputs of evaluation:

| | Score | Prediction |
|---|---|---|
| **What** | A number (0.0 to 1.0) measuring quality | The actual output the agent produced |
| **Stored in** | `gen_X/<domain>_eval/report.json` | `gen_X/<domain>_eval/predictions.json` |
| **Used for** | Ranking generations, parent selection | Returning results to users |
| **Example** | `0.85` | `"echo hello world"` |

The `ensemble` function (`hyperflow/core/ensemble.py`) uses both: it finds the highest-scoring generation using scores, then returns that generation's prediction for a specific question.

---

## Executors

Executors (`hyperflow/utils/executor.py`) provide isolated environments for each generation to run in.

### Local Executor
- Creates a temp directory, copies the repo
- Applies patches, runs the MetaAgent
- Fast, good for development
- No isolation — MetaAgent edits real files

### Docker Executor
- Spins up a container per generation
- Applies patches inside the container
- Safe for untrusted LLM-generated code
- Slower but fully isolated

```python
from hyperflow import create_executor

executor = create_executor("local", {"repoPath": ".", "baseCommit": "HEAD"})
# or
executor = create_executor("docker", {"repoPath": ".", "imageName": "hyperflow"})
```

Both implement the same interface:
```python
class Executor(ABC):
    def setup(self, patch_files: list[str]) -> None: ...    # Create workspace, apply patches
    def get_workdir(self) -> str: ...                       # Path to the working directory
    def diff(self) -> str: ...                              # Get changes as a diff/patch
    def copy_out(self, src: str, dst: str) -> None: ...     # Copy files out of the workspace
    def cleanup(self) -> None: ...                          # Remove workspace
```

---

## File System Layout

### During Evolution

```
outputs/bash_evolution/
├── archive.jsonl                    ← The archive (one snapshot per line)
├── gen_initial/
│   └── metadata.json                ← { prev_patch_files: [], curr_patch_files: [] }
├── gen_1/
│   ├── metadata.json                ← { parent_genid: "initial", run_eval: true, ... }
│   ├── agent_output/
│   │   └── model_patch.diff         ← The patch MetaAgent produced
│   └── bash_eval/
│       ├── predictions.json         ← [{ questionId, prediction, score }, ...]
│       └── report.json              ← { averageScore: 0.73, ... }
├── gen_2/
│   ├── metadata.json
│   ├── agent_output/
│   │   └── model_patch.diff
│   └── bash_eval/
│       ├── predictions.json
│       └── report.json
└── ...
```

### During Single Eval

```
outputs/bash_eval/
├── predictions.json                 ← What the agent predicted
└── report.json                      ← Score summary
```

No archive, no metadata, no patches — just the evaluation results.

---

## JSONL vs JSON

| | JSON | JSONL (JSON Lines) |
|---|---|---|
| Structure | One object per file | One object per **line** |
| Appending | Must rewrite entire file | Just append a new line |
| Reading latest | Must parse everything | Read only the **last line** |
| History | Only current state | **Every snapshot** preserved |
| Used for | `report.json`, `metadata.json`, `predictions.json` | `archive.jsonl` |

The archive uses JSONL because it's **append-friendly**. Each time a new generation is added, a new line is appended instead of rewriting the whole file. And you get a complete history for free.

---

## Self-Referential Improvement (Prompt Files)

A core concept from the HyperAgents paper is **self-referential self-improvement** — the MetaAgent can modify its own instructions to become a better improver.

### The Problem

When HyperFlow is installed as a pip package, all framework code lives in `site-packages/` (immutable). The MetaAgent can't edit its own prompt because it's hardcoded in the package.

### The Solution: Editable Prompt Files

Both agents support loading prompts from **files in the user's workspace** instead of hardcoded defaults:

```python
from hyperflow import MetaAgent, TaskAgent, AgentOptions

# Option 1: Pass prompt_file directly to agents
meta_agent = MetaAgent(AgentOptions(model=model, prompt_file="./prompts/meta_agent.txt"))
task_agent = TaskAgent(AgentOptions(model=model, prompt_file="./prompts/task_agent.txt"))

# Option 2: Use prompts_dir in the generate loop (auto-scaffolds files)
config = GenerateLoopConfig(
    # ...
    prompts_dir="./prompts",  # creates meta_agent.txt + task_agent.txt
)
```

When `prompts_dir` is set, the loop automatically creates default prompt files if they don't exist. The MetaAgent can then edit these files — including its own prompt.

### Template Variables

Prompt files support `{{variable}}` placeholders that are filled at runtime:

**`meta_agent.txt`** variables:
- `{{repoPath}}` — path to the codebase being modified
- `{{evalPath}}` — path to evaluation results
- `{{iterationsContext}}` — "You have N iterations remaining..."
- `{{scoreContext}}` — "The current agent scores X%..."

**`task_agent.txt`** variables:
- `{{inputs}}` — JSON-formatted task inputs

### Self-Modification in Action

```
Gen 1: MetaAgent reads meta_agent.txt
       "You are an expert AI agent engineer..."
       → Edits TaskAgent prompt → score 0.6
       → Also edits meta_agent.txt: adds "Focus on edge cases first"

Gen 2: MetaAgent reads updated meta_agent.txt
       "You are an expert AI agent engineer... Focus on edge cases first"
       → Makes better-targeted edits → score 0.85

Gen 3: MetaAgent reads meta_agent.txt again
       → Refines its own approach further → score 0.95
```

The MetaAgent gets better at improving things because it can improve its own instructions. This is the "self-referential" part — the improver improves itself.

### Without prompts_dir (Default)

If `prompts_dir` is not set, prompts use the hardcoded defaults. The system still works — the MetaAgent just can't modify its own prompt. It can still modify everything else in the user's repo (domain code, tools, task prompts stored as separate files, etc.).

---

## Early Termination

The evolutionary loop includes two smart optimizations:

### 1. Perfect Score Stop
Before each generation, the loop checks if the best score in the archive has reached 1.0 (100%). If so, it stops — no point improving a perfect agent.

```
gen 1: score 0.7  → continue
gen 2: score 1.0  → "Perfect score achieved. Stopping early."
gen 3: never runs (saved compute + API costs)
```

### 2. Score-Aware MetaAgent
The MetaAgent receives the parent's current score in its prompt:
- **Score < 100%**: "The current agent scores 70.0%. Focus on failing tasks."
- **Score = 100%**: "All tasks passing. Do NOT make changes unless you identify a clear improvement."

This prevents the MetaAgent from making unnecessary (or harmful) changes when the agent is already performing well.

---

## Examples Overview

| Example | What it demonstrates | Uses `run_generate_loop`? | Mode |
|---|---|---|---|
| **scoring** | Prompt improvement (string matching → math equivalence) | No (manual loop) | evaluate → improve → evaluate |
| **calculator** | Tool improvement (fix buggy calculator) | No (manual loop) | evaluate → improve → evaluate |
| **bash** | Bash command generation | Yes (both modes) | `eval` or `evolve` |
| **factcheck** | True/false classification of common myths | Yes (both modes) | `eval` or `evolve` |
| **paper_review** | Accept/reject predictions for papers | Custom | single eval |
| **git_evolution** | Full evolutionary loop with git-based patches | Yes | evolve |

### Running Examples

```bash
# Single evaluation (one-shot, no improvement)
cd examples/bash && python run.py
cd examples/scoring && python run.py
cd examples/calculator && python run.py

# Evolutionary self-improvement (multiple generations)
cd examples/bash && python run.py evolve
cd examples/factcheck && python run.py evolve
cd examples/git_evolution && python run.py
```

---

## Glossary

| Term | Definition |
|---|---|
| **Archive** | The JSONL file storing the history of all generations and their scores |
| **Domain** | A task category with its own evaluation logic (bash, scoring, factcheck, etc.) |
| **Evaluator** | A function that scores a prediction (static, LLM judge, or human feedback) |
| **Executor** | An isolated environment (local or Docker) where code modifications happen |
| **Generation** | One iteration of the evolutionary loop, producing a new agent version |
| **Harness** | The generic evaluation runner that connects agents to domain tasks |
| **MetaAgent** | The AI agent that reads failures and edits source code to improve the TaskAgent |
| **Parent** | The generation whose code state is used as the starting point for a new generation |
| **Patch** | A diff file capturing the code changes a generation made |
| **Prediction** | The actual output the TaskAgent produces for a task |
| **Score** | A 0-1 number measuring how well a generation performed |
| **Selection Strategy** | The algorithm for choosing which generation to improve next |
| **TaskAgent** | The AI agent that solves domain-specific tasks |
| **JSONL** | JSON Lines format — one JSON object per line, append-friendly |
| **Local Maximum** | A solution that's better than its neighbors but not the best overall |
| **Global Maximum** | The best possible solution across all approaches |
| **MAP-Elites / QD** | Quality-Diversity algorithms from evolutionary computation that inspired this architecture |
