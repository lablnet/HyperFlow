"""Framework tools for HyperFlow agents.

@since v1.0.0
@author Muhammad Umer Farooq <umer@lablnet.com>
"""
from __future__ import annotations

from langchain_core.tools import StructuredTool

from .bash import create_bash_tool
from .editor import create_editor_tool

__all__ = ["create_bash_tool", "create_editor_tool", "get_framework_tools"]


def get_framework_tools() -> list[StructuredTool]:
    """Get the standard framework tools needed by the MetaAgent
    to modify codebases in the self-improvement loop.
    """
    return [create_bash_tool(), create_editor_tool()]
