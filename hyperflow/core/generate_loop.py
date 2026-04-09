"""Main evolutionary self-improvement driver.

This is the Python port of HyperAgents' generate_loop.ts.
Each generation:
  1. Select a parent from the archive
  2. Set up an executor (local or Docker)
  3. Apply lineage diffs
  4. Run the MetaAgent to produce code modifications
  5. Evaluate the produced agent (staged then full)
  6. Update the archive
  7. Repeat

@since v1.0.0
@author Muhammad Umer Farooq <umer@lablnet.com>
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

from langchain_core.tools import BaseTool

from ..agent.meta_agent import MetaAgent
from ..agent.task_agent import TaskAgent
from ..core.select_parent import SelectionStrategy, select_parent
from ..domains.base import Domain
from ..domains.harness import HarnessOptions, run_harness
from ..domains.report import ReportOptions, generate_report
from ..prompts.meta_agent import META_AGENT_PROMPT_TEMPLATE, MetaAgentPromptOptions
from ..prompts.task_agent import TASK_AGENT_PROMPT_TEMPLATE
from ..utils.archive import (
    ArchiveEntry,
    get_avg_score,
    get_best_score,
    get_patch_files,
    load_archive,
    save_gen_metadata,
    update_archive,
)
from ..utils.common import ensure_dir
from ..utils.constants import PATCH_FILENAME
from ..utils.executor import create_executor


@dataclass
class GenerateLoopConfig:
    domains: list[Domain]
    meta_agent: MetaAgent
    task_agent_factory: Callable[[list[BaseTool]], TaskAgent]
    tools: list[BaseTool]
    output_dir: str
    repo_path: str
    max_generations: int
    execution_mode: str  # "local" | "docker"
    parent_selection: SelectionStrategy
    domain_factory: Optional[Callable[[str], list[Domain]]] = None
    """Optional: create fresh domain instances pointing at the executor's workdir after MetaAgent edits."""
    eval_samples: int = -1
    eval_workers: int = 1
    base_commit: str = "HEAD"
    image_name: Optional[str] = None
    skip_staged_eval: bool = False
    prompts_dir: Optional[str] = None
    """Directory containing editable prompt files (meta_agent.txt, task_agent.txt).
    If set, prompts are read from these files at runtime, enabling the MetaAgent
    to modify its own prompt and the TaskAgent's prompt across generations."""


async def run_generate_loop(config: GenerateLoopConfig) -> str:
    """Run the full evolutionary self-improvement loop.

    Each generation:
      1. Select a parent from the archive
      2. Set up an executor (local or Docker)
      3. Apply lineage diffs
      4. Run the MetaAgent to produce code modifications
      5. Evaluate the produced agent (staged then full)
      6. Update the archive
      7. Repeat

    Args:
        config: The configuration for the generate loop.

    Returns:
        The path to the output directory.

    @since v1.0.0
    @author Muhammad Umer Farooq <umer@lablnet.com>
    """

    # Destructure the configuration.
    domains = config.domains
    meta_agent = config.meta_agent
    task_agent_factory = config.task_agent_factory
    tools = config.tools
    output_dir = config.output_dir
    repo_path = config.repo_path
    max_generations = config.max_generations
    execution_mode = config.execution_mode
    parent_selection = config.parent_selection
    eval_samples = config.eval_samples
    eval_workers = config.eval_workers
    base_commit = config.base_commit
    skip_staged_eval = config.skip_staged_eval
    prompts_dir = config.prompts_dir

    # Ensure the output directory exists, otherwise create it.
    ensure_dir(output_dir)

    # Resolve prompt file paths (if promptsDir is configured).
    meta_prompt_file = os.path.join(prompts_dir, "meta_agent.txt") if prompts_dir else None
    task_prompt_file = os.path.join(prompts_dir, "task_agent.txt") if prompts_dir else None

    # Scaffold default prompt files if promptsDir is set but files don't exist yet.
    if prompts_dir:
        ensure_dir(prompts_dir)
        if meta_prompt_file and not os.path.exists(meta_prompt_file):
            Path(meta_prompt_file).write_text(META_AGENT_PROMPT_TEMPLATE, encoding="utf-8")
            print(f"Scaffolded editable prompt: {meta_prompt_file}")
        if task_prompt_file and not os.path.exists(task_prompt_file):
            Path(task_prompt_file).write_text(TASK_AGENT_PROMPT_TEMPLATE, encoding="utf-8")
            print(f"Scaffolded editable prompt: {task_prompt_file}")

    # Get the names of the domains.
    domain_names = [d.config.name for d in domains]

    # Load the archive data.
    archive = load_archive(output_dir)

    # If the archive is empty, create an initial entry.
    if not archive.archive:
        initial_entry = ArchiveEntry(
            gen_id="initial",
            parent_id=None,
            patch_files=[],
            scores={},
            metadata={"run_eval": True},
            valid_parent=True,
            timestamp=datetime.now().isoformat(),
        )
        archive = update_archive(output_dir, archive, initial_entry)
        ensure_dir(os.path.join(output_dir, "gen_initial"))
        save_gen_metadata(
            output_dir,
            "initial",
            {
                "gen_output_dir": os.path.join(output_dir, "gen_initial"),
                "prev_patch_files": [],
                "curr_patch_files": [],
                "run_eval": True,
            },
        )

    # Loop through the generations.
    for gen_id in range(len(archive.archive), max_generations + 1):
        # Early termination: check if the best score in the archive is perfect.
        best_archive_score = get_best_score(archive, output_dir, domain_names)
        if best_archive_score >= 1.0:
            print(f"\nPerfect score ({best_archive_score * 100:.1f}%) achieved. Stopping early.")
            break

        print(f"\n=== Generation {gen_id} ===")

        # Select a parent generation.
        parent_id = select_parent(archive, output_dir, domain_names, parent_selection)
        print(f"Selected parent: {parent_id}")

        # Create the generation directory.
        gen_dir = os.path.join(output_dir, f"gen_{gen_id}")
        ensure_dir(gen_dir)

        # Create the executor.
        executor = create_executor(
            execution_mode,
            {
                "repoPath": repo_path,
                "baseCommit": base_commit,
                "imageName": config.image_name,
                "containerName": f"hyperflow-gen-{gen_id}-{int(time.time() * 1000)}",
            },
        )

        # Get the previous patch files.
        prev_patch_files = get_patch_files(output_dir, parent_id)
        curr_patch_files: list[str] = []
        run_eval = False
        parent_agent_success = False

        try:
            # Setup the executor.
            executor.setup(prev_patch_files)

            # Compute the parent's average score across domains.
            parent_score = get_avg_score(output_dir, parent_id, domain_names)

            # Run the meta agent with score context and optional prompt file.
            _ = await meta_agent.forward(
                MetaAgentPromptOptions(
                    repo_path=executor.get_workdir(),
                    eval_path=output_dir,
                    iterations_left=max_generations - gen_id,
                    parent_score=parent_score,
                    prompt_file=meta_prompt_file,
                )
            )

            parent_agent_success = True

            diff_output = executor.diff()
            patch_file = os.path.join(gen_dir, "agent_output", PATCH_FILENAME)
            ensure_dir(os.path.dirname(patch_file))

            if diff_output.strip():
                Path(patch_file).write_text(diff_output, encoding="utf-8")
                curr_patch_files = [patch_file]
                run_eval = True
                print(f"  Captured diff: {len(diff_output.splitlines())} lines")
            else:
                print("  No code changes detected.")
                run_eval = False

            if run_eval:
                task_agent = task_agent_factory(tools)

                # Use domainFactory to create domains from the edited workdir, so
                # MetaAgent's file edits (e.g. prompt.txt) are picked up by evaluation.
                eval_domains = config.domain_factory(executor.get_workdir()) if config.domain_factory else domains

                for domain in eval_domains:
                    eval_dir = os.path.join(gen_dir, f"{domain.config.name}_eval")
                    ensure_dir(eval_dir)

                    num_samples: int | None
                    if skip_staged_eval:
                        num_samples = eval_samples if eval_samples > 0 else None
                    else:
                        num_samples = domain.config.staged_eval_samples

                    harness_result = await run_harness(
                        HarnessOptions(
                            domain=domain,
                            agent=task_agent,
                            subset=domain.config.eval_subsets[0] if domain.config.eval_subsets else "train",
                            num_samples=num_samples if num_samples is not None else -1,
                            num_workers=eval_workers,
                            output_dir=eval_dir,
                        )
                    )

                    generate_report(
                        ReportOptions(
                            domain=domain.config.name,
                            output_dir=eval_dir,
                            results=harness_result.results,
                        )
                    )

                    print(f"  {domain.config.name}: score={harness_result.score:.4f}")

        except Exception as err:
            print(f"Generation {gen_id} failed: {err}")
            run_eval = False
        finally:
            executor.cleanup()

        # Create the metadata.
        metadata = {
            "gen_output_dir": gen_dir,
            "current_genid": gen_id,
            "parent_genid": parent_id,
            "prev_patch_files": prev_patch_files,
            "curr_patch_files": curr_patch_files,
            "parent_agent_success": parent_agent_success,
            "run_eval": run_eval,
            "valid_parent": run_eval,
        }
        save_gen_metadata(output_dir, gen_id, metadata)

        # Initialize the scores.
        scores: dict[str, float] = {}
        for domain in domains:
            eval_dir = os.path.join(gen_dir, f"{domain.config.name}_eval")
            report_path = os.path.join(eval_dir, "report.json")
            if os.path.exists(report_path):
                report = json.loads(Path(report_path).read_text(encoding="utf-8"))
                scores[domain.config.name] = report.get("averageScore", 0)

        # Create the archive entry.
        entry = ArchiveEntry(
            gen_id=gen_id,
            parent_id=parent_id,
            patch_files=[*prev_patch_files, *curr_patch_files],
            scores=scores,
            metadata=metadata,
            valid_parent=run_eval,
            timestamp=datetime.now().isoformat(),
        )
        archive = update_archive(output_dir, archive, entry)

        # Log the scores.
        print(f"Generation {gen_id} complete. Scores: {json.dumps(scores)}")

    print(f"\nGenerate loop complete. Output: {output_dir}")
    return output_dir
