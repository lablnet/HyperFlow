"""HyperFlow Paper Review Example.

@since v1.0.0
@author Muhammad Umer Farooq <umer@lablnet.com>
"""
from __future__ import annotations

import asyncio
import os
import sys

from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from hyperflow.agent.task_agent import TaskAgent
from hyperflow.agent.base_agent import AgentOptions
from hyperflow.domains.harness import HarnessOptions, run_harness
from hyperflow.domains.report import ReportOptions, generate_report
from hyperflow.utils.common import ensure_dir

from domain import PaperReviewDomain


async def main() -> None:
    print("=== HyperFlow Paper Review Example ===\n")

    model = os.environ.get("HYPERFLOW_MODEL", "anthropic/claude-sonnet-4-5-20250929")

    task_agent = TaskAgent(AgentOptions(model=model))
    domain = PaperReviewDomain()

    output_dir = "./outputs/paper_review_eval"
    ensure_dir(output_dir)

    print(f"Model: {model}")
    print("Loading tasks...\n")

    result = await run_harness(
        HarnessOptions(
            domain=domain,
            agent=task_agent,
            subset="train",
            num_samples=4,
            output_dir=output_dir,
        )
    )

    report = generate_report(
        ReportOptions(domain="paper_review", output_dir=output_dir, results=result.results)
    )

    print("\n=== Results ===")
    print(f"Tasks evaluated: {report.total_tasks}")
    print(f"Average Score: {report.average_score:.2f}")

    for r in result.results:
        if r.score == 1.0:
            icon = "OK"
        elif r.score == 0.5:
            icon = "PARTIAL"
        else:
            icon = "MISS"
        print(f'  [{icon}] {r.question_id}: predicted="{r.prediction}"')


if __name__ == "__main__":
    asyncio.run(main())
