"""MetaAgent modifies the codebase to produce improved TaskAgents.

It receives the repo path and evaluation history, then uses tools
(bash, editor, etc.) to modify any part of the codebase. This is
the "mutation operator" in the evolutionary self-improvement loop.

Framework tools (bash + editor) are loaded automatically if no
tools are explicitly provided. You can pass additional tools
and they'll be merged with the framework tools.

@since v1.0.0
@author Muhammad Umer Farooq <umer@lablnet.com>
"""

from __future__ import annotations

from typing import Any

from .base_agent import AgentOptions, AgentSystem
from .llm_with_tools import ChatWithAgentOptions, chat_with_agent
from ..prompts.meta_agent import MetaAgentPromptOptions, meta_agent_prompt
from ..tools import get_framework_tools


class MetaAgent(AgentSystem):
    """MetaAgent modifies the codebase to produce improved TaskAgents.

    Framework tools (bash + editor) are loaded automatically if no
    tools are explicitly provided. You can pass additional tools
    and they'll be merged with the framework tools.
    """

    def __init__(self, options: AgentOptions | None = None) -> None:
        """Create a new MetaAgent.

        Args:
            options: The options for the MetaAgent.

        @since v1.0.0
        @author Muhammad Umer Farooq <umer@lablnet.com>
        """
        super().__init__(options)
        self._prompt_file = options.prompt_file if options else None

        if not options or not options.tools:
            self._tool_registry.register_many(get_framework_tools())

    async def forward(self, options: MetaAgentPromptOptions | dict[str, Any]) -> str:
        """Forward the input to the MetaAgent.

        Args:
            options: The options for the MetaAgent (MetaAgentPromptOptions or dict).

        Returns:
            The output of the MetaAgent.

        @since v1.0.0
        @author Muhammad Umer Farooq <umer@lablnet.com>
        """
        if isinstance(options, dict):
            opts = MetaAgentPromptOptions(
                repo_path=options["repoPath"],
                eval_path=options["evalPath"],
                iterations_left=options.get("iterationsLeft"),
                parent_score=options.get("parentScore"),
                prompt_file=options.get("promptFile", self._prompt_file),
            )
        else:
            opts = options
            if opts.prompt_file is None:
                opts.prompt_file = self._prompt_file

        instruction = meta_agent_prompt(opts)
        tools = self._tool_registry.get_all()

        result = await chat_with_agent(
            instruction,
            ChatWithAgentOptions(
                llm=self._llm,
                tools=tools,
                log=self._log,
            ),
        )

        return result.response
