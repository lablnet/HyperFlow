"""Multi-provider LLM construction.

@since v1.0.0
@author Muhammad Umer Farooq <umer@lablnet.com>
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

from langchain_core.language_models.chat_models import BaseChatModel

# The models supported by the LLM.
MODELS = {
    "CLAUDE_SONNET": "anthropic/claude-sonnet-4-5-20250929",
    "CLAUDE_HAIKU": "anthropic/claude-3-haiku-20240307",
    "OPENAI_GPT4O": "openai/gpt-4o",
    "OPENAI_GPT4O_MINI": "openai/gpt-4o-mini",
    "OPENAI_O3": "openai/o3",
    "OPENAI_O3_MINI": "openai/o3-mini",
    "OPENAI_O4_MINI": "openai/o4-mini",
    "GEMINI_PRO": "gemini/gemini-2.5-pro",
    "GEMINI_FLASH": "gemini/gemini-2.5-flash",
    "OLLAMA_LLAMA3": "ollama/llama3",
}

ModelId = str


@dataclass
class LLMConfig:
    """Configuration for an LLM."""

    model: str
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None


def _parse_model_id(model: str) -> tuple[str, str]:
    """Parse the model ID into a provider and model name.

    Args:
        model: The model ID.

    Returns:
        Tuple of (provider, model_name).

    @since v1.0.0
    @author Muhammad Umer Farooq <umer@lablnet.com>
    """
    slash_index = model.find("/")
    if slash_index == -1:
        raise ValueError(f'Invalid model format "{model}". Expected "provider/model-name" (e.g. "openai/gpt-4o").')
    return model[:slash_index], model[slash_index + 1 :]


def create_llm(config: LLMConfig) -> BaseChatModel:
    """Create a new LLM model.

    Args:
        config: The configuration of the LLM.

    Returns:
        The LLM model.

    @since v1.0.0
    @author Muhammad Umer Farooq <umer@lablnet.com>
    """
    provider, model_name = _parse_model_id(config.model)
    temperature = config.temperature if config.temperature is not None else 0.0
    max_tokens = config.max_tokens if config.max_tokens is not None else 16384

    if provider == "openai":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    if provider == "anthropic":
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(
            model=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    if provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(
            model=model_name,
            temperature=temperature,
            max_output_tokens=max_tokens,
        )

    if provider == "ollama":
        from langchain_ollama import ChatOllama

        return ChatOllama(
            base_url=os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434"),
            model=model_name,
            temperature=temperature,
        )

    raise ValueError(f'Unsupported provider "{provider}". Supported: openai, anthropic, gemini, ollama.')
