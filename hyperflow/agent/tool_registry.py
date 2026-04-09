"""A registry for tools that can be used by the agent.

@since v1.0.0
@author Muhammad Umer Farooq <umer@lablnet.com>

Example::

    tool_registry = ToolRegistry()
    tool_registry.register(some_tool)
    tool_registry.register(another_tool)
"""

from __future__ import annotations

from langchain_core.tools import BaseTool


class ToolRegistry:
    """A registry for tools that can be used by the agent."""

    def __init__(self) -> None:
        self._tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        """Register a new tool.

        Args:
            tool: The tool to register.

        @since v1.0.0
        @author Muhammad Umer Farooq <umer@lablnet.com>
        """
        self._tools[tool.name] = tool

    def register_many(self, tools: list[BaseTool]) -> None:
        """Register multiple tools.

        Args:
            tools: The tools to register.

        @since v1.0.0
        @author Muhammad Umer Farooq <umer@lablnet.com>
        """
        for tool in tools:
            self.register(tool)

    def get(self, name: str) -> BaseTool | None:
        """Get a tool by name.

        Args:
            name: The name of the tool.

        Returns:
            The tool, or None if not found.

        @since v1.0.0
        @author Muhammad Umer Farooq <umer@lablnet.com>
        """
        return self._tools.get(name)

    def get_all(self) -> list[BaseTool]:
        """Get all tools.

        Returns:
            The list of tools.

        @since v1.0.0
        @author Muhammad Umer Farooq <umer@lablnet.com>
        """
        return list(self._tools.values())

    def has(self, name: str) -> bool:
        """Check if a tool is registered.

        Args:
            name: The name of the tool.

        Returns:
            True if the tool is registered, False otherwise.

        @since v1.0.0
        @author Muhammad Umer Farooq <umer@lablnet.com>
        """
        return name in self._tools

    def names(self) -> list[str]:
        """Get all tool names.

        Returns:
            The tool names.

        @since v1.0.0
        @author Muhammad Umer Farooq <umer@lablnet.com>
        """
        return list(self._tools.keys())

    def clear(self) -> None:
        """Clear the tool registry.

        @since v1.0.0
        @author Muhammad Umer Farooq <umer@lablnet.com>
        """
        self._tools.clear()
