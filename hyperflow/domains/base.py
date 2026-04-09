"""Domain interface -- the contract every evaluation domain must implement.

Each example (bash, paper_review, etc.) provides its own Domain class
that knows how to load tasks, format inputs, evaluate predictions,
and generate reports.

@since v1.0.0
@author Muhammad Umer Farooq <umer@lablnet.com>
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class DomainTask:
    """A single task in a domain."""

    question_id: str
    domain: str
    inputs: dict[str, Any]
    ground_truth: Optional[str] = None


@dataclass
class DomainConfig:
    """Configuration for a domain."""

    name: str
    eval_subsets: list[str]
    splits: list[str]
    staged_eval_samples: int
    score_key: str


@dataclass
class EvalResult:
    """Result of evaluating a single task."""

    question_id: str
    prediction: str
    score: float
    metadata: Optional[dict[str, Any]] = None


@dataclass
class ReportSummary:
    """Summary of evaluation results for a domain."""

    domain: str
    subset: str
    total_tasks: int
    average_score: float
    scores: dict[str, Any] = field(default_factory=dict)


class Domain(ABC):
    """Domain interface -- the contract every evaluation domain must implement."""

    config: DomainConfig

    @abstractmethod
    async def load_tasks(self, subset: str, num_samples: int | None = None) -> list[DomainTask]: ...

    @abstractmethod
    async def evaluate(self, prediction: str, task: DomainTask) -> float: ...

    @abstractmethod
    def format_input(self, task: DomainTask) -> str: ...

    @abstractmethod
    async def report(self, results: list[EvalResult]) -> ReportSummary: ...
