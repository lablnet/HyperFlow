"""Abstract base class for all agent systems.

@since v1.0.0
@author Muhammad Umer Farooq <umer@lablnet.com>
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Optional

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.tools import BaseTool

from .llm import LLMConfig, create_llm
from .tool_registry import ToolRegistry


@dataclass
class AgentOptions:
    model: Optional[str] = None
    llm_config: Optional[LLMConfig] = None
    llm: Optional[BaseChatModel] = None
    tools: Optional[list[BaseTool]] = None
    log_file: Optional[str] = None
    prompt_file: Optional[str] = None
    """Path to a prompt file. If set, the agent reads its system prompt from this file
    at runtime instead of using the hardcoded default. This enables the MetaAgent
    to edit prompt files in the user's workspace -- including its own."""


class AgentSystem(ABC):
    """A base class for all agent systems.

    @since v1.0.0
    @author Muhammad Umer Farooq <umer@lablnet.com>
    """

    def __init__(self, options: AgentOptions | None = None) -> None:
        """Create a new agent system.

        Args:
            options: The options for the agent.

        @since v1.0.0
        @author Muhammad Umer Farooq <umer@lablnet.com>
        """
        opts = options or AgentOptions()
        self._model = opts.model or "openai/gpt-4o"
        self._llm = opts.llm or create_llm(opts.llm_config or LLMConfig(model=self._model))
        self._tool_registry = ToolRegistry()

        if opts.tools:
            self._tool_registry.register_many(opts.tools)

        self._log = self._create_logger(opts.log_file)

    def _create_logger(self, log_file: str | None = None) -> Callable[..., None]:
        """Create a logger for the agent.

        Args:
            log_file: The file to log to.

        Returns:
            The logger function.

        @since v1.0.0
        @author Muhammad Umer Farooq <umer@lablnet.com>
        """
        if not log_file:

            def _console_log(*args: Any) -> None:
                print("[HyperFlow]", *args)

            return _console_log

        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        def _file_log(*args: Any) -> None:
            line = " ".join(a if isinstance(a, str) else json.dumps(a) for a in args)
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(f"{datetime.now().isoformat()} {line}\n")
            print("[HyperFlow]", *args)

        return _file_log

    @abstractmethod
    async def forward(self, *args: Any, **kwargs: Any) -> Any:
        """Forward the input to the agent.

        Args:
            *args: Positional arguments.
            **kwargs: Keyword arguments.

        Returns:
            The output of the agent.

        @since v1.0.0
        @author Muhammad Umer Farooq <umer@lablnet.com>
        """
        ...
