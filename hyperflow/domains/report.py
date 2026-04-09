"""Generate score reports from evaluation results.

@since v1.0.0
@author Muhammad Umer Farooq <umer@lablnet.com>
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .base import EvalResult, ReportSummary


@dataclass
class ReportOptions:
    domain: str
    output_dir: str
    results: Optional[list[EvalResult]] = None


def generate_report(options: ReportOptions) -> ReportSummary:
    """Generate a score report from evaluation results.

    Args:
        options: The report options.

    Returns:
        The report summary.
    """
    domain = options.domain
    output_dir = options.output_dir
    results = options.results

    if results is None:
        predictions_path = os.path.join(output_dir, "predictions.json")
        if not os.path.exists(predictions_path):
            raise FileNotFoundError(f"No predictions found at {predictions_path}")
        raw = json.loads(Path(predictions_path).read_text(encoding="utf-8"))
        results = [
            EvalResult(
                question_id=r["questionId"],
                prediction=r["prediction"],
                score=r["score"],
            )
            for r in raw
        ]

    total_tasks = len(results)
    total_score = sum(r.score for r in results)
    average_score = total_score / total_tasks if total_tasks > 0 else 0.0

    scores = {
        "average": average_score,
        "total": total_score,
        "count": total_tasks,
    }

    summary = ReportSummary(
        domain=domain,
        subset=os.path.basename(output_dir),
        total_tasks=total_tasks,
        average_score=average_score,
        scores=scores,
    )

    os.makedirs(output_dir, exist_ok=True)
    report_path = os.path.join(output_dir, "report.json")
    Path(report_path).write_text(
        json.dumps(
            {
                "domain": summary.domain,
                "subset": summary.subset,
                "totalTasks": summary.total_tasks,
                "averageScore": summary.average_score,
                "scores": summary.scores,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    return summary
