"""HyperFlow -- a self-improving agent framework built on LangChain and LangGraph.

Python port of HyperAgents (TypeScript).
"""

# Agent
from .agent.base_agent import AgentOptions, AgentSystem
from .agent.llm import MODELS, LLMConfig, ModelId, create_llm
from .agent.llm_with_tools import ChatResult, ChatWithAgentOptions, chat_with_agent
from .agent.meta_agent import MetaAgent
from .agent.task_agent import TaskAgent
from .agent.tool_registry import ToolRegistry

# Prompts
from .prompts.llm_judge import LLMJudgePromptOptions, llm_judge_prompt
from .prompts.meta_agent import META_AGENT_PROMPT_TEMPLATE, MetaAgentPromptOptions, meta_agent_prompt
from .prompts.task_agent import TASK_AGENT_PROMPT_TEMPLATE, TaskAgentPromptOptions, task_agent_prompt

# Tools
from .tools import get_framework_tools
from .tools.bash import create_bash_tool
from .tools.editor import create_editor_tool

# Core
from .core.ensemble import ensemble
from .core.generate_loop import GenerateLoopConfig, run_generate_loop
from .core.select_parent import SelectionStrategy, select_parent

# Domains
from .domains.base import Domain, DomainConfig, DomainTask, EvalResult, ReportSummary
from .domains.evaluators import (
    EvaluatorType,
    human_feedback_evaluator,
    llm_judge_evaluator,
    static_evaluator,
)
from .domains.harness import HarnessOptions, HarnessResult, run_harness
from .domains.report import ReportOptions, generate_report

# Utils
from .utils.archive import (
    ArchiveData,
    ArchiveEntry,
    get_avg_score,
    get_best_score,
    load_archive,
    save_archive,
    update_archive,
)
from .utils.common import ensure_dir, extract_jsons, file_exists_and_not_empty, load_json_file
from .utils.constants import ARCHIVE_FILENAME, DEFAULT_OUTPUT_DIR, PATCH_FILENAME, REPO_NAME
from .utils.docker import DockerConfig, DockerManager
from .utils.executor import DockerExecutor, Executor, LocalExecutor, create_executor
from .utils.git import apply_patch, apply_patches, create_git_ops, diff_versus_commit, hard_reset

__all__ = [
    # Agent
    "AgentOptions",
    "AgentSystem",
    "ChatResult",
    "ChatWithAgentOptions",
    "LLMConfig",
    "MODELS",
    "MetaAgent",
    "ModelId",
    "TaskAgent",
    "ToolRegistry",
    "chat_with_agent",
    "create_llm",
    # Prompts
    "LLMJudgePromptOptions",
    "META_AGENT_PROMPT_TEMPLATE",
    "MetaAgentPromptOptions",
    "TASK_AGENT_PROMPT_TEMPLATE",
    "TaskAgentPromptOptions",
    "llm_judge_prompt",
    "meta_agent_prompt",
    "task_agent_prompt",
    # Tools
    "create_bash_tool",
    "create_editor_tool",
    "get_framework_tools",
    # Core
    "GenerateLoopConfig",
    "SelectionStrategy",
    "ensemble",
    "run_generate_loop",
    "select_parent",
    # Domains
    "Domain",
    "DomainConfig",
    "DomainTask",
    "EvalResult",
    "EvaluatorType",
    "HarnessOptions",
    "HarnessResult",
    "ReportOptions",
    "ReportSummary",
    "generate_report",
    "human_feedback_evaluator",
    "llm_judge_evaluator",
    "run_harness",
    "static_evaluator",
    # Utils
    "ARCHIVE_FILENAME",
    "ArchiveData",
    "ArchiveEntry",
    "DEFAULT_OUTPUT_DIR",
    "DockerConfig",
    "DockerExecutor",
    "DockerManager",
    "Executor",
    "LocalExecutor",
    "PATCH_FILENAME",
    "REPO_NAME",
    "apply_patch",
    "apply_patches",
    "create_executor",
    "create_git_ops",
    "diff_versus_commit",
    "ensure_dir",
    "extract_jsons",
    "file_exists_and_not_empty",
    "get_avg_score",
    "get_best_score",
    "hard_reset",
    "load_archive",
    "load_json_file",
    "save_archive",
    "update_archive",
]
