"""Generic evaluation harness -- runs a TaskAgent against a Domain's tasks
and collects predictions + scores.

@since v1.0.0
@author Muhammad Umer Farooq <umer@lablnet.com>
"""

from __future__ import annotations

import asyncio
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from .base import Domain, DomainTask, EvalResult

if TYPE_CHECKING:
    from ..agent.task_agent import TaskAgent


@dataclass
class HarnessOptions:
    domain: Domain
    agent: TaskAgent
    subset: str
    num_samples: int = -1
    num_workers: int = 1
    output_dir: str = ""


@dataclass
class HarnessResult:
    results: list[EvalResult]
    score: float


async def run_harness(options: HarnessOptions) -> HarnessResult:
    """Generic evaluation harness -- runs a TaskAgent against a Domain's tasks
    and collects predictions + scores.

    Args:
        options: The harness options.

    Returns:
        The harness results.
    """
    domain = options.domain
    agent = options.agent
    subset = options.subset
    num_samples = options.num_samples
    num_workers = options.num_workers
    output_dir = options.output_dir

    tasks = await domain.load_tasks(subset, num_samples if num_samples > 0 else None)
    results: list[EvalResult] = []

    async def process_task(task: DomainTask) -> EvalResult:
        formatted_input = domain.format_input(task)

        task_result = await agent.forward(
            {
                "domain": domain.config.name,
                **task.inputs,
                "formattedInput": formatted_input,
            }
        )

        score = await domain.evaluate(task_result["prediction"], task)

        return EvalResult(
            question_id=task.question_id,
            prediction=task_result["prediction"],
            score=score,
        )

    if num_workers <= 1:
        for task in tasks:
            result = await process_task(task)
            results.append(result)
    else:
        # Process in chunks of num_workers concurrently
        for i in range(0, len(tasks), num_workers):
            chunk = tasks[i : i + num_workers]
            chunk_results = await asyncio.gather(*(process_task(t) for t in chunk))
            results.extend(chunk_results)

    total_score = sum(r.score for r in results)
    average_score = total_score / len(results) if results else 0.0

    os.makedirs(output_dir, exist_ok=True)
    predictions_data = [{"questionId": r.question_id, "prediction": r.prediction, "score": r.score} for r in results]
    Path(os.path.join(output_dir, "predictions.json")).write_text(
        json.dumps(predictions_data, indent=2), encoding="utf-8"
    )

    return HarnessResult(results=results, score=average_score)
