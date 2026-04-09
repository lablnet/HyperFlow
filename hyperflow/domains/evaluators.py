"""Evaluator functions: static, LLM judge, human feedback.

@since v1.0.0
@author Muhammad Umer Farooq <umer@lablnet.com>
"""

from __future__ import annotations

import json
from typing import Any, Literal

from ..agent.llm import LLMConfig, create_llm
from ..prompts.llm_judge import LLMJudgePromptOptions, llm_judge_prompt
from ..utils.common import extract_jsons

EvaluatorType = Literal["static", "llm_judge", "human"]


def static_evaluator(prediction: str, ground_truth: str) -> float:
    """Static evaluator: exact string match after normalization.
    Free, fast, deterministic. Use for tasks with single correct answers.

    Args:
        prediction: The predicted answer.
        ground_truth: The expected answer.

    Returns:
        1.0 if match, 0.0 otherwise.
    """
    pred = prediction.lower().strip()
    expected = ground_truth.lower().strip()
    return 1.0 if pred == expected else 0.0


async def llm_judge_evaluator(
    prediction: str,
    task: dict[str, Any],
    config: LLMConfig | None = None,
) -> float:
    """LLM judge evaluator: asks an LLM to score the prediction.
    Use for subjective tasks where there's no single right answer
    (e.g., "generate tasks from email", "write a review", "summarize text").

    The judge LLM scores on a 0-1 scale based on quality, relevance, and correctness.

    Args:
        prediction: The agent's prediction.
        task: Dict with ``description``, optional ``groundTruth``, optional ``rubric``.
        config: Optional LLM configuration override.

    Returns:
        Score between 0.0 and 1.0.
    """
    llm = create_llm(config or LLMConfig(model="openai/gpt-4o", temperature=0))

    prompt = llm_judge_prompt(
        LLMJudgePromptOptions(
            description=task["description"],
            ground_truth=task.get("groundTruth"),
            rubric=task.get("rubric"),
            prediction=prediction,
        )
    )

    response = await llm.ainvoke(prompt)
    text = response.content if isinstance(response.content, str) else json.dumps(response.content)

    try:
        extracted = extract_jsons(text)
        if extracted and "score" in extracted[-1]:
            score = float(extracted[-1]["score"])
            return max(0.0, min(1.0, score))
    except Exception:
        pass  # fallback

    return 0.0


def human_feedback_evaluator(feedback_score: float) -> float:
    """Human feedback evaluator: returns a score from user-provided feedback.
    Use when collecting ratings from real users.

    This is a simple wrapper -- in production you'd connect this
    to your feedback collection system (database, API, etc.).

    Args:
        feedback_score: The feedback score.

    Returns:
        Score clamped between 0.0 and 1.0.
    """
    return max(0.0, min(1.0, feedback_score))
