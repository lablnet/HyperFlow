"""LangGraph ReAct chat loop.

@since v1.0.0
@author Muhammad Umer Farooq <umer@lablnet.com>
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_core.tools import BaseTool
from langgraph.prebuilt import create_react_agent


@dataclass
class ChatWithAgentOptions:
    llm: BaseChatModel
    tools: list[BaseTool]
    system_prompt: Optional[str] = None
    max_tool_calls: int = 40
    log: Callable[..., Any] = print


@dataclass
class ChatResult:
    response: str
    messages: list[BaseMessage] = field(default_factory=list)


async def chat_with_agent(
    input_text: str,
    options: ChatWithAgentOptions,
) -> ChatResult:
    """Run a ReAct-style agentic loop using LangGraph.

    The LLM reasons about the task, decides which tools to call,
    observes tool outputs, and repeats until it produces a final answer.

    Args:
        input_text: The input to the agent.
        options: The options for the agent.

    Returns:
        The result of the chat with the agent.

    @since v1.0.0
    @author Muhammad Umer Farooq <umer@lablnet.com>
    """
    llm = options.llm
    tools = options.tools
    system_prompt = options.system_prompt
    max_tool_calls = options.max_tool_calls
    log = options.log

    agent = create_react_agent(
        model=llm,
        tools=tools,
        prompt=system_prompt,
    )

    log(f"[chatWithAgent] Input: {input_text[:200]}...")

    result = await agent.ainvoke(
        {"messages": [HumanMessage(content=input_text)]},
        config={"recursion_limit": max_tool_calls * 2 + 10},
    )

    messages: list[BaseMessage] = result["messages"]
    last_message = messages[-1]
    response = last_message.content if isinstance(last_message.content, str) else json.dumps(last_message.content)

    log(f"[chatWithAgent] Response: {response[:200]}...")

    return ChatResult(response=response, messages=messages)
