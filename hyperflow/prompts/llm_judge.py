"""LLM Judge prompt template.

@since v1.0.0
@author Muhammad Umer Farooq <umer@lablnet.com>
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class LLMJudgePromptOptions:
    description: str
    ground_truth: Optional[str] = None
    rubric: Optional[str] = None
    prediction: str = ""


def llm_judge_prompt(options: LLMJudgePromptOptions) -> str:
    """Default prompt for the LLMJudge.

    Args:
        options: The options for the LLMJudge.

    Returns:
        The prompt for the LLMJudge.

    @since v1.0.0
    @author Muhammad Umer Farooq <umer@lablnet.com>
    """
    ground_truth_section = f"\nExpected/reference answer: {options.ground_truth}" if options.ground_truth else ""
    rubric_section = f"\nScoring rubric: {options.rubric}" if options.rubric else ""

    return f"""You are an impartial judge evaluating an AI agent's output.

Task description: {options.description}{ground_truth_section}{rubric_section}

Agent's output:
{options.prediction}

Score this output on a scale from 0.0 to 1.0:
- 1.0 = perfect, fully correct and complete
- 0.5 = partially correct or incomplete
- 0.0 = wrong or irrelevant

Consider: accuracy, completeness, relevance, and quality.

Respond ONLY with JSON: {{ "score": <number>, "reason": "<brief explanation>" }}"""
