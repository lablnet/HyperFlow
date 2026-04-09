"""Bash domain: evaluate bash command generation.

@since v1.0.0
@author Muhammad Umer Farooq <umer@lablnet.com>
"""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Optional

from hyperflow.domains.base import (
    Domain,
    DomainConfig,
    DomainTask,
    EvalResult,
    ReportSummary,
)

CONFIG = DomainConfig(
    name="bash",
    eval_subsets=["train"],
    splits=["train"],
    staged_eval_samples=5,
    score_key="accuracy",
)


class BashDomain(Domain):
    config = CONFIG

    def __init__(self, tasks_path: str | None = None) -> None:
        self._tasks_path = tasks_path or os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "tasks.json"
        )

    async def load_tasks(self, subset: str, num_samples: int | None = None) -> list[DomainTask]:
        raw = json.loads(Path(self._tasks_path).read_text(encoding="utf-8"))

        tasks: list[DomainTask] = [
            DomainTask(
                question_id=t["id"],
                domain="bash",
                inputs={
                    "description": t["description"],
                    "hint": t.get("hint", ""),
                },
                ground_truth=t["expected_output"],
            )
            for t in raw
        ]

        if num_samples and num_samples > 0:
            return tasks[:num_samples]
        return tasks

    async def evaluate(self, prediction: str, task: DomainTask) -> float:
        try:
            result = subprocess.run(
                prediction,
                shell=True,
                executable="/bin/bash",
                capture_output=True,
                text=True,
                timeout=30,
            )
            output = result.stdout.strip()
            expected = (task.ground_truth or "").strip()
            return 1.0 if output == expected else 0.0
        except Exception:
            return 0.0

    def format_input(self, task: DomainTask) -> str:
        desc = task.inputs["description"]
        hint = task.inputs.get("hint", "")
        hint_section = f"\nHint: {hint}" if hint else ""
        return (
            f"Write a bash one-liner or short script that does the following:\n\n"
            f"{desc}{hint_section}\n\n"
            f"Your response must be valid bash that can be executed directly.\n"
            f'Respond in JSON format: {{ "response": "<your bash command>" }}'
        )

    async def report(self, results: list[EvalResult]) -> ReportSummary:
        total = len(results)
        correct = sum(1 for r in results if r.score == 1.0)
        accuracy = correct / total if total > 0 else 0.0

        return ReportSummary(
            domain="bash",
            subset="train",
            total_tasks=total,
            average_score=accuracy,
            scores={"accuracy": accuracy, "correct": correct, "total": total},
        )
