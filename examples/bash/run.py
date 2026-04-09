"""HyperFlow Bash Example: Single Evaluation + Evolutionary Self-Improvement.

@since v1.0.0
@author Muhammad Umer Farooq <umer@lablnet.com>
"""
from __future__ import annotations

import asyncio
import os
import sys

from dotenv import load_dotenv

load_dotenv()

# Allow running from the examples/ directory without installing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from hyperflow.agent.meta_agent import MetaAgent
from hyperflow.agent.task_agent import TaskAgent
from hyperflow.agent.base_agent import AgentOptions
from hyperflow.core.generate_loop import GenerateLoopConfig, run_generate_loop
from hyperflow.domains.harness import HarnessOptions, run_harness
from hyperflow.domains.report import ReportOptions, generate_report
from hyperflow.tools import get_framework_tools
from hyperflow.utils.common import ensure_dir

from domain import BashDomain


async def run_single_eval() -> None:
    print("=== HyperFlow Bash Example: Single Evaluation ===\n")

    model = os.environ.get("HYPERFLOW_MODEL", "openai/gpt-4o")

    # TaskAgent gets framework tools so it can execute bash commands
    task_agent = TaskAgent(AgentOptions(model=model, tools=get_framework_tools()))
    domain = BashDomain()

    output_dir = "./outputs/bash_eval"
    ensure_dir(output_dir)

    result = await run_harness(
        HarnessOptions(
            domain=domain,
            agent=task_agent,
            subset="train",
            num_samples=3,
            output_dir=output_dir,
        )
    )

    report = generate_report(
        ReportOptions(domain="bash", output_dir=output_dir, results=result.results)
    )

    print("\n=== Results ===")
    print(f"Tasks: {report.total_tasks}")
    print(f"Average Score: {report.average_score:.2f}")
    print(f"Scores: {report.scores}")


async def run_evolutionary_loop() -> None:
    print("=== HyperFlow Bash Example: Evolutionary Self-Improvement ===\n")

    model = os.environ.get("HYPERFLOW_MODEL", "anthropic/claude-sonnet-4-5-20250929")
    tools = get_framework_tools()

    # MetaAgent auto-loads framework tools even without passing them,
    # but we pass them here explicitly for the TaskAgent factory too.
    meta_agent = MetaAgent(AgentOptions(model=model))
    domain = BashDomain()

    config = GenerateLoopConfig(
        domains=[domain],
        meta_agent=meta_agent,
        task_agent_factory=lambda t: TaskAgent(AgentOptions(model=model, tools=t)),
        tools=tools,
        output_dir="./outputs/bash_evolution",
        repo_path=".",
        max_generations=3,
        execution_mode="local",
        parent_selection="score_child_prop",
        eval_samples=5,
    )

    output_dir = await run_generate_loop(config)
    print(f"\nEvolution complete. Results at: {output_dir}")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "eval"

    if mode == "evolve":
        asyncio.run(run_evolutionary_loop())
    else:
        asyncio.run(run_single_eval())
