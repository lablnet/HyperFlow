"""Paper review domain: evaluate accept/reject prediction.

@since v1.0.0
@author Muhammad Umer Farooq <umer@lablnet.com>
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from hyperflow.domains.base import (
    Domain,
    DomainConfig,
    DomainTask,
    EvalResult,
    ReportSummary,
)

CONFIG = DomainConfig(
    name="paper_review",
    eval_subsets=["train"],
    splits=["train"],
    staged_eval_samples=5,
    score_key="accuracy",
)


class PaperReviewDomain(Domain):
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
                domain="paper_review",
                inputs={
                    "title": t["title"],
                    "abstract": t["abstract"],
                    "venue": t["venue"],
                },
                ground_truth=t["decision"],
            )
            for t in raw
        ]

        if num_samples and num_samples > 0:
            return tasks[:num_samples]
        return tasks

    async def evaluate(self, prediction: str, task: DomainTask) -> float:
        expected = (task.ground_truth or "").lower().strip()
        pred = prediction.lower().strip()

        if pred == expected:
            return 1.0
        if expected in pred:
            return 0.5
        return 0.0

    def format_input(self, task: DomainTask) -> str:
        return (
            f"You are an expert paper reviewer for the {task.inputs['venue']} venue.\n\n"
            f"Review the following paper and predict whether it will be accepted or rejected.\n\n"
            f"Title: {task.inputs['title']}\n\n"
            f"Abstract: {task.inputs['abstract']}\n\n"
            f"Based on the quality, novelty, and significance of this work, predict the decision.\n"
            f'Respond in JSON format: {{ "response": "accept" }} or {{ "response": "reject" }}'
        )

    async def report(self, results: list[EvalResult]) -> ReportSummary:
        total = len(results)
        correct = sum(1 for r in results if r.score == 1.0)
        partial = sum(1 for r in results if r.score == 0.5)
        total_score = sum(r.score for r in results)
        accuracy = total_score / total if total > 0 else 0.0

        return ReportSummary(
            domain="paper_review",
            subset="train",
            total_tasks=total,
            average_score=accuracy,
            scores={"accuracy": accuracy, "correct": correct, "partial": partial, "total": total},
        )
