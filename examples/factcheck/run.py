"""HyperFlow Fact-Check Example: Single Evaluation + Evolutionary Loop.

@since v1.0.0
@author Muhammad Umer Farooq <umer@lablnet.com>
"""
from __future__ import annotations

import asyncio
import json
import os
import sys

from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from hyperflow.agent.meta_agent import MetaAgent
from hyperflow.agent.task_agent import TaskAgent
from hyperflow.agent.base_agent import AgentOptions
from hyperflow.core.generate_loop import GenerateLoopConfig, run_generate_loop
from hyperflow.domains.harness import HarnessOptions, run_harness
from hyperflow.domains.report import ReportOptions, generate_report
from hyperflow.tools import get_framework_tools
from hyperflow.utils.common import ensure_dir

from domain import FactCheckDomain


async def run_single_eval() -> None:
    """Mode 1: Single evaluation -- run the TaskAgent on fact-check tasks once
    and print the score. No evolution, no archive, just "how good is it now?"
    """
    print("=== HyperFlow Fact-Check Example: Single Evaluation ===\n")

    model = os.environ.get("HYPERFLOW_MODEL", "anthropic/claude-sonnet-4-5-20250929")
    task_agent = TaskAgent(AgentOptions(model=model, tools=get_framework_tools()))
    domain = FactCheckDomain()

    output_dir = "./outputs/factcheck_eval"
    ensure_dir(output_dir)

    result = await run_harness(
        HarnessOptions(
            domain=domain,
            agent=task_agent,
            subset="train",
            num_samples=5,
            output_dir=output_dir,
        )
    )

    report = generate_report(
        ReportOptions(domain="factcheck", output_dir=output_dir, results=result.results)
    )

    print("\n=== Results ===")
    print(f"Tasks: {report.total_tasks}")
    print(f"Average Score: {report.average_score:.2f}")
    print(f"Scores: {report.scores}")

    print("\n=== Per-task breakdown ===")
    for r in result.results:
        icon = "PASS" if r.score == 1.0 else "FAIL"
        print(f'  [{icon}] {r.question_id}: predicted="{r.prediction}"')


async def run_evolutionary_loop() -> None:
    """Mode 2: Evolutionary self-improvement loop -- uses runGenerateLoop
    with the archive, parent selection, MetaAgent, and harness evaluation.

    Each generation:
      1. Picks the best parent from the archive
      2. MetaAgent analyses failures and edits the code/prompts
      3. Harness evaluates the modified agent on fact-check tasks
      4. Scores are recorded in the archive
      5. Repeat for N generations
    """
    print("=== HyperFlow Fact-Check Example: Evolutionary Self-Improvement ===\n")

    model = os.environ.get("HYPERFLOW_MODEL", "openai/gpt-4o")
    tools = get_framework_tools()
    meta_agent = MetaAgent(AgentOptions(model=model))
    domain = FactCheckDomain()

    config = GenerateLoopConfig(
        domains=[domain],
        meta_agent=meta_agent,
        task_agent_factory=lambda t: TaskAgent(AgentOptions(model=model, tools=t)),
        tools=tools,
        output_dir="./outputs/factcheck_evolution",
        repo_path=".",
        max_generations=3,
        execution_mode="local",
        parent_selection="score_child_prop",
        eval_samples=10,
    )

    output_dir = await run_generate_loop(config)
    print(f"\nEvolution complete. Results at: {output_dir}")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "eval"

    if mode == "evolve":
        asyncio.run(run_evolutionary_loop())
    else:
        asyncio.run(run_single_eval())
