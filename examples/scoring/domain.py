"""Scoring domain: evaluate accept/reject grading.

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
    name="scoring",
    eval_subsets=["train"],
    splits=["train"],
    staged_eval_samples=6,
    score_key="accuracy",
)


class ScoringDomain(Domain):
    config = CONFIG

    def __init__(self, tasks_path: str | None = None) -> None:
        self._tasks_path = tasks_path or os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "tasks.json"
        )
        self._repo_dir = os.path.dirname(self._tasks_path)

    async def load_tasks(self, subset: str, num_samples: int | None = None) -> list[DomainTask]:
        raw = json.loads(Path(self._tasks_path).read_text(encoding="utf-8"))

        tasks: list[DomainTask] = [
            DomainTask(
                question_id=t["id"],
                domain="scoring",
                inputs={
                    "question": t["question"],
                    "student_answer": t["student_answer"],
                    "expected_answer": t["expected_answer"],
                },
                ground_truth="accept" if t["correct"] else "reject",
            )
            for t in raw
        ]

        if num_samples and num_samples > 0:
            return tasks[:num_samples]
        return tasks

    async def evaluate(self, prediction: str, task: DomainTask) -> float:
        expected = (task.ground_truth or "").lower().strip()
        pred = prediction.lower().strip()
        return 1.0 if pred == expected else 0.0

    def get_prompt(self) -> str:
        prompt_path = os.path.join(self._repo_dir, "prompt.txt")
        if os.path.exists(prompt_path):
            return Path(prompt_path).read_text(encoding="utf-8")
        return 'Grade the answer. Respond with JSON: { "response": "accept" } or { "response": "reject" }'

    def format_input(self, task: DomainTask) -> str:
        prompt = self.get_prompt()
        return (
            f"{prompt}\n\n"
            f"Question: {task.inputs['question']}\n"
            f"Expected answer: {task.inputs['expected_answer']}\n"
            f"Student answer: {task.inputs['student_answer']}\n\n"
            f'Respond with JSON: {{ "response": "accept" }} or {{ "response": "reject" }}'
        )

    async def report(self, results: list[EvalResult]) -> ReportSummary:
        total = len(results)
        correct = sum(1 for r in results if r.score == 1.0)
        accuracy = correct / total if total > 0 else 0.0

        return ReportSummary(
            domain="scoring",
            subset="train",
            total_tasks=total,
            average_score=accuracy,
            scores={"accuracy": accuracy, "correct": correct, "total": total},
        )
