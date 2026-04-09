"""HyperFlow Git-Based Evolution Demo.

Git-based evolution demo using the framework's own run_generate_loop().

This sets up a mini git repo, then runs the full evolutionary loop:
  - LocalExecutor copies repo to /tmp/ (originals safe)
  - MetaAgent edits files in /tmp/
  - git diff captures changes as .diff patches
  - Patches saved in archive
  - Next generation applies ancestor patches on fresh copy

Your source files are NEVER modified.

@since v1.0.0
@author Muhammad Umer Farooq <umer@lablnet.com>
"""
from __future__ import annotations

import asyncio
import os
import shutil
import subprocess
import sys

from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from hyperflow.agent.meta_agent import MetaAgent
from hyperflow.agent.task_agent import TaskAgent
from hyperflow.agent.base_agent import AgentOptions
from hyperflow.core.generate_loop import GenerateLoopConfig, run_generate_loop
from hyperflow.tools import get_framework_tools
from hyperflow.utils.common import ensure_dir

from domain import ScoringDomain

OUTPUT_DIR = os.path.abspath("./outputs/git_evolution")
REPO_DIR = os.path.join(OUTPUT_DIR, "repo")

WEAK_PROMPT = (
    "Compare the student answer to the expected answer.\n"
    'If the strings are EXACTLY identical character by character, respond "accept".\n'
    'Otherwise respond "reject". Do NOT interpret mathematical equivalence.'
)


def setup_repo() -> None:
    if os.path.exists(os.path.join(REPO_DIR, ".git")):
        print(f"Using existing repo at: {REPO_DIR}\n")
        return

    ensure_dir(REPO_DIR)
    subprocess.run(["git", "init"], cwd=REPO_DIR, capture_output=True, check=True)
    subprocess.run(
        ["git", "config", "user.email", "demo@hyperflow"],
        cwd=REPO_DIR, capture_output=True, check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "HyperFlow Demo"],
        cwd=REPO_DIR, capture_output=True, check=True,
    )

    Path(os.path.join(REPO_DIR, "prompt.txt")).write_text(WEAK_PROMPT, encoding="utf-8")

    tasks_src = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tasks.json")
    shutil.copyfile(tasks_src, os.path.join(REPO_DIR, "tasks.json"))

    subprocess.run(
        ["git", "add", "-A"],
        cwd=REPO_DIR, capture_output=True, check=True,
    )
    subprocess.run(
        ["git", "commit", "-m", "initial: weak grading prompt"],
        cwd=REPO_DIR, capture_output=True, check=True,
    )

    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=REPO_DIR, capture_output=True, text=True, check=True,
    ).stdout.strip()
    print(f"Git repo initialized at: {REPO_DIR}")
    print(f"Base commit: {commit}\n")


async def main() -> None:
    force_reset = "--reset" in sys.argv

    if force_reset:
        shutil.rmtree(OUTPUT_DIR, ignore_errors=True)
        print("Reset: cleaned everything.\n")

    print("=== HyperFlow: Git-Based Evolution Demo ===")
    print("Uses run_generate_loop() + LocalExecutor + git diff.")
    print("Edits happen in /tmp/. Originals never touched.")
    print("Patches saved as .diff files in the archive.\n")

    setup_repo()

    model = os.environ.get("HYPERFLOW_MODEL", "openai/gpt-4o")

    # Find a numeric argument for generations count
    generations = 2
    for arg in sys.argv[1:]:
        if arg.isdigit():
            generations = int(arg)
            break

    base_commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=REPO_DIR, capture_output=True, text=True, check=True,
    ).stdout.strip()

    config = GenerateLoopConfig(
        domains=[ScoringDomain(os.path.join(REPO_DIR, "tasks.json"))],
        domain_factory=lambda workdir: [ScoringDomain(os.path.join(workdir, "tasks.json"))],
        meta_agent=MetaAgent(AgentOptions(model=model)),
        task_agent_factory=lambda tools: TaskAgent(AgentOptions(model=model, tools=tools)),
        tools=get_framework_tools(),
        output_dir=OUTPUT_DIR,
        repo_path=REPO_DIR,
        max_generations=generations,
        execution_mode="local",
        parent_selection="best",
        base_commit=base_commit,
        skip_staged_eval=True,
    )

    output_dir = await run_generate_loop(config)

    print(f"\nOriginal repo untouched:")
    original_prompt = Path(os.path.join(REPO_DIR, "prompt.txt")).read_text(encoding="utf-8")
    print(f'  "{original_prompt.splitlines()[0]}..."\n')

    gen_dirs = sorted(
        d for d in os.listdir(OUTPUT_DIR) if d.startswith("gen_")
    )
    print("Archive contents:")
    for gen_dir in gen_dirs:
        patch_path = os.path.join(OUTPUT_DIR, gen_dir, "agent_output", "model_patch.diff")
        if os.path.exists(patch_path):
            size = os.path.getsize(patch_path)
            print(f"  {gen_dir}: patch ({size} bytes)")
        else:
            print(f"  {gen_dir}: no patch")
    print(f"\nRun again to add more generations. Use --reset to start over.")


if __name__ == "__main__":
    asyncio.run(main())
