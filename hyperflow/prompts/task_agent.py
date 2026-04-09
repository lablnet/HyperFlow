"""TaskAgent prompt template.

@since v1.0.0
@author Muhammad Umer Farooq <umer@lablnet.com>
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

TASK_AGENT_PROMPT_TEMPLATE = """You are an agent.

Task input:
```
{{inputs}}
```

Perform a strict character-by-character comparison of the inputs. Respond in JSON format with the following schema:

{
    "response": ...
}"""


@dataclass
class TaskAgentPromptOptions:
    inputs: dict[str, Any]
    prompt_file: Optional[str] = None


def task_agent_prompt(
    inputs: dict[str, Any] | TaskAgentPromptOptions,
) -> str:
    """Default prompt for the TaskAgent.
    Receives task inputs and instructs the LLM to respond in JSON.
    If a promptFile is provided and exists, uses that template instead.

    Args:
        inputs: The inputs to the TaskAgent, or a TaskAgentPromptOptions object.

    Returns:
        The prompt for the TaskAgent.

    @since v1.0.0
    @author Muhammad Umer Farooq <umer@lablnet.com>
    """
    prompt_file: str | None = None
    task_inputs: dict[str, Any]

    if isinstance(inputs, TaskAgentPromptOptions):
        prompt_file = inputs.prompt_file
        task_inputs = inputs.inputs
    else:
        task_inputs = inputs

    input_json = json.dumps(task_inputs, indent=2)

    template = TASK_AGENT_PROMPT_TEMPLATE
    if prompt_file and os.path.exists(prompt_file):
        template = Path(prompt_file).read_text(encoding="utf-8")

    return template.replace("{{inputs}}", input_json)
