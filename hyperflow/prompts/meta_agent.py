"""MetaAgent prompt template.

@since v1.0.0
@author Muhammad Umer Farooq <umer@lablnet.com>
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

META_AGENT_PROMPT_TEMPLATE = """You are an expert AI agent engineer. Your goal is to improve the agent system.

Modify any part of the codebase at `{{repoPath}}`.

Previous evaluation results are available at `{{evalPath}}`. Analyze them to understand what works and what doesn't, then make targeted improvements.
{{iterationsContext}}{{scoreContext}}
Focus on changes that will improve task performance. You can modify:
- The task agent's logic and prompts
- How inputs are processed
- How outputs are formatted
- Any utility functions
- This prompt file itself (to improve how you approach future improvements)

After making changes, briefly explain what you changed and why."""


@dataclass
class MetaAgentPromptOptions:
    repo_path: str
    eval_path: str
    iterations_left: Optional[int] = None
    parent_score: Optional[float] = None
    prompt_file: Optional[str] = None


def meta_agent_prompt(options: MetaAgentPromptOptions) -> str:
    """Default prompt for the MetaAgent.
    Instructs the LLM to analyze evaluations and modify the codebase.
    When the parent score is perfect (1.0), instructs the agent to skip changes.

    Args:
        options: The options for the MetaAgent.

    Returns:
        The prompt for the MetaAgent.

    @since v1.0.0
    @author Muhammad Umer Farooq <umer@lablnet.com>
    """
    iterations_context = ""
    if options.iterations_left is not None:
        iterations_context = f"\nYou have {options.iterations_left} iterations remaining to improve the agent."

    score_context = ""
    if options.parent_score is not None:
        pct = f"{options.parent_score * 100:.1f}"
        if options.parent_score >= 1.0:
            score_context = (
                f"\nThe current agent scores {pct}% (all tasks passing). Do NOT make changes "
                f"unless you identify a clear robustness or efficiency improvement. If everything "
                f'looks good, respond with "No changes needed." and make no edits.'
            )
        else:
            score_context = f"\nThe current agent scores {pct}%. Focus your improvements on the failing tasks."

    template = META_AGENT_PROMPT_TEMPLATE
    if options.prompt_file and os.path.exists(options.prompt_file):
        template = Path(options.prompt_file).read_text(encoding="utf-8")

    return (
        template.replace("{{repoPath}}", options.repo_path)
        .replace("{{evalPath}}", options.eval_path)
        .replace("{{iterationsContext}}", iterations_context)
        .replace("{{scoreContext}}", score_context)
    )
