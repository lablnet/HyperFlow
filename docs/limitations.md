# Limitations

While HyperFlow enables powerful self-improving agents, several technical and practical limitations exist in the current implementation.

### Frozen Foundation Models
The most significant limitation is that **the underlying Large Language Model (LLM) is frozen**. 
- HyperFlow improves the **Agent Logic** (Python code, prompts, and tools), but it **cannot** update the weights or training of the model itself. 
- All improvements are "external" to the model's core architecture.

### Framework Immutability (Self-Update Paradox)
**The Agent cannot evolve its own core classes!**
Because HyperFlow is often installed as a library (via `pip`), the core code for `TaskAgent` and `MetaAgent` lives in the system's `site-packages`.
- The MetaAgent **cannot** modify its own framework code or its class definitions.
- Even in a local setup, the evolutionary loop targets a specific `repo_path`. If the agent's primary logic is outside that directory, it is **impossible** for the MetaAgent to reach out and update itself.
- This is why the framework focuses on evolving **prompts in external files** and **local domain logic**—the core "Agent" infrastructure remains static and generic.

### Fixed Task Distribution
Currently, the system optimizes for a **fixed set of tasks** provided by the user. Truly unbounded open-endedness requires a system that can also generate its own tasks and curriculum (co-evolution), which is a future research direction.

### Static Outer Loop
While the agent can modify almost all of its own codebase, the **outer evolutionary process** is currently human-engineered:
- **Parent Selection**: The logic for choosing which generations to branch from is fixed.
- **Evaluation Protocols**: The way task scripts are run and scored is defined in the initial configuration.

### Computational Cost
Evolutionary computation is resource-intensive. 
- **Generations**: Each experiment typically requires 50-200 iterations.
- **Costs**: Depending on the Foundation Model (FM) used, a full run can be expensive in terms of API tokens and local GPU compute.

### Sandboxing & Security
Self-modifying code must be executed in a **sandbox** (e.g., Docker). 
- **Latency**: Running tasks in isolated environments adds overhead to the evaluation loop.
- **Escapes**: Although Docker is used, absolute security against sophisticated "adversarial" self-modification is an ongoing area of study.

### Overfitting
Without a diverse "Validation" set, a MetaAgent might discover "cheats" or heuristics that score highly on training data but fail to generalize to real-world tasks. Proper split management (Train/Val/Test) is essential.
