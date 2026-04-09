"""TaskAgent solves domain-specific tasks.

In the original HyperAgents, the TaskAgent is intentionally minimal
so the MetaAgent can easily modify its behavior via code patches.

@since v1.0.0
@author Muhammad Umer Farooq <umer@lablnet.com>
"""

from __future__ import annotations

import json
from typing import Any

from .base_agent import AgentOptions, AgentSystem
from .llm_with_tools import ChatWithAgentOptions, chat_with_agent
from ..prompts.task_agent import TaskAgentPromptOptions, task_agent_prompt
from ..utils.common import extract_jsons


class TaskAgent(AgentSystem):
    """TaskAgent solves domain-specific tasks.

    In the original HyperAgents, the TaskAgent is intentionally minimal
    so the MetaAgent can easily modify its behavior via code patches.
    """

    def __init__(self, options: AgentOptions | None = None) -> None:
        super().__init__(options)
        self._prompt_file = options.prompt_file if options else None

    async def forward(self, inputs: dict[str, Any]) -> dict[str, Any]:
        """Forward the input to the TaskAgent.

        Args:
            inputs: The input to the TaskAgent (must contain ``domain`` key).

        Returns:
            Dict with ``prediction`` (str) and ``messageHistory`` (list).

        @since v1.0.0
        @author Muhammad Umer Farooq <umer@lablnet.com>
        """
        if self._prompt_file:
            instruction = task_agent_prompt(TaskAgentPromptOptions(inputs=inputs, prompt_file=self._prompt_file))
        else:
            instruction = task_agent_prompt(inputs)

        tools = self._tool_registry.get_all()

        result = await chat_with_agent(
            instruction,
            ChatWithAgentOptions(
                llm=self._llm,
                tools=tools,
                log=self._log,
            ),
        )

        prediction = "None"
        try:
            extracted = extract_jsons(result.response)
            if extracted and "response" in extracted[-1]:
                prediction = str(extracted[-1]["response"])
        except Exception as e:
            self._log(f"Error extracting prediction: {e}")

        message_history = [
            {
                "role": m.type,
                "text": m.content if isinstance(m.content, str) else json.dumps(m.content),
            }
            for m in result.messages
        ]

        return {
            "prediction": prediction,
            "messageHistory": message_history,
        }
