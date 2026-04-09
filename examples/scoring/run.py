"""HyperFlow Scoring Example: Self-Improvement Demo (Math Grading).

The MetaAgent edits real source files to improve the agent.

@since v1.0.0
@author Muhammad Umer Farooq <umer@lablnet.com>
"""
from __future__ import annotations

import asyncio
import json
import os
import shutil
import sys

from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from hyperflow.agent.llm import LLMConfig, create_llm
from hyperflow.agent.llm_with_tools import ChatWithAgentOptions, chat_with_agent
from hyperflow.agent.meta_agent import MetaAgent
from hyperflow.agent.base_agent import AgentOptions
from hyperflow.prompts.meta_agent import MetaAgentPromptOptions
from hyperflow.utils.common import ensure_dir, extract_jsons

EXAMPLE_DIR = os.path.dirname(os.path.abspath(__file__))
PROMPT_FILE = os.path.join(EXAMPLE_DIR, "prompt.txt")
EVAL_DIR = os.path.abspath("./outputs/scoring_eval")

INITIAL_PROMPT = (
    "Compare the student's answer to the expected answer.\n"
    'If the two strings are EXACTLY identical character-by-character, respond "accept".\n'
    "If they differ in ANY way -- extra spaces, trailing zeros, fractions vs decimals -- "
    'respond "reject".\n'
    "Do NOT interpret mathematical equivalence. Only do raw string comparison."
)


def get_prompt() -> str:
    if os.path.exists(PROMPT_FILE):
        return Path(PROMPT_FILE).read_text(encoding="utf-8")
    return INITIAL_PROMPT


def load_tasks() -> list[dict]:
    return json.loads(Path(os.path.join(EXAMPLE_DIR, "tasks.json")).read_text(encoding="utf-8"))


async def evaluate(generation: int) -> dict:
    model = os.environ.get("HYPERFLOW_MODEL", "anthropic/claude-sonnet-4-5-20250929")
    llm = create_llm(LLMConfig(model=model, temperature=0))
    system_prompt = get_prompt()

    print(f"\n--- Generation {generation} ---")
    source = "prompt.txt" if os.path.exists(PROMPT_FILE) else "INITIAL_PROMPT in run.py"
    print(f"Prompt (from {source}):")
    for line in system_prompt.splitlines():
        print(f"  | {line}")
    print()

    tasks = load_tasks()
    details: list[str] = []
    correct = 0

    for task in tasks:
        user_message = (
            f"Question: {task['question']}\n"
            f"Expected answer: {task['expected_answer']}\n"
            f"Student answer: {task['student_answer']}\n\n"
            'Is the student\'s answer correct? Respond ONLY with JSON: '
            '{ "response": "accept" } or { "response": "reject" }'
        )

        result = await chat_with_agent(
            user_message,
            ChatWithAgentOptions(
                llm=llm,
                tools=[],
                system_prompt=system_prompt,
                log=lambda *a: None,
            ),
        )

        prediction = "unknown"
        try:
            extracted = extract_jsons(result.response)
            if extracted and "response" in extracted[-1]:
                prediction = str(extracted[-1]["response"]).lower().strip()
        except Exception:
            prediction = "accept" if "accept" in result.response.lower() else "reject"

        truth = "accept" if task["correct"] else "reject"
        is_correct = prediction == truth
        if is_correct:
            correct += 1

        icon = "PASS" if is_correct else "FAIL"
        line = (
            f'  [{icon}] {task["id"]}: student="{task["student_answer"]}" '
            f'expected="{task["expected_answer"]}" -> predicted="{prediction}" (truth: {truth})'
        )
        details.append(line)
        print(line)

    score = correct / len(tasks) if tasks else 0
    print(f"\n  Score: {score:.2f} ({correct}/{len(tasks)})\n")

    eval_dir = os.path.join(EVAL_DIR, f"gen_{generation}")
    ensure_dir(eval_dir)
    Path(os.path.join(eval_dir, "results.txt")).write_text(
        "\n".join([
            f"Generation {generation} Results: {score:.2f} ({correct}/{len(tasks)})",
            "",
            "System prompt used:",
            system_prompt,
            "",
            "All results:",
            *details,
            "",
            "FAILURES that need fixing:",
            *[d for d in details if "[FAIL]" in d],
            "",
            f"The prompt file is at: {PROMPT_FILE}",
            f"The example source code is at: {EXAMPLE_DIR}",
            "You can edit prompt.txt, run.py, domain.py, or tasks.json to improve performance.",
        ]),
        encoding="utf-8",
    )

    return {"score": score, "details": details}


async def improve() -> None:
    model = os.environ.get("HYPERFLOW_MODEL", "openai/gpt-4o")

    print("=== MetaAgent analyzing failures and improving the code ===\n")

    # If no prompt.txt exists yet, write the initial one so MetaAgent can edit it
    if not os.path.exists(PROMPT_FILE):
        Path(PROMPT_FILE).write_text(INITIAL_PROMPT, encoding="utf-8")

    # Copy eval results into the example dir so MetaAgent can find them
    eval_results_target = os.path.join(EXAMPLE_DIR, "eval_results")
    ensure_dir(eval_results_target)
    if os.path.exists(EVAL_DIR):
        shutil.copytree(EVAL_DIR, eval_results_target, dirs_exist_ok=True)

    meta_agent = MetaAgent(AgentOptions(model=model))

    # Point MetaAgent at the REAL source directory -- it will edit actual files
    await meta_agent.forward(
        MetaAgentPromptOptions(
            repo_path=EXAMPLE_DIR,
            eval_path=EXAMPLE_DIR,
            iterations_left=1,
        )
    )

    # Clean up copied eval results
    shutil.rmtree(eval_results_target, ignore_errors=True)

    print("\nMetaAgent finished editing.\n")

    new_prompt = get_prompt()
    print("Current prompt after edit:")
    for line in new_prompt.splitlines():
        print(f"  | {line}")
    print()


def get_generation_count() -> int:
    if not os.path.exists(EVAL_DIR):
        return 0
    return len([d for d in os.listdir(EVAL_DIR) if d.startswith("gen_")])


async def main() -> None:
    force_reset = "--reset" in sys.argv

    if force_reset:
        # Reset prompt.txt back to the weak version
        Path(PROMPT_FILE).write_text(INITIAL_PROMPT, encoding="utf-8")
        shutil.rmtree(EVAL_DIR, ignore_errors=True)
        print("Reset to initial weak prompt.\n")

    gen_start = get_generation_count()

    print("=== HyperFlow: Self-Improvement Demo (Math Grading) ===")
    print("The MetaAgent edits real source files to improve the agent.")
    if gen_start == 0:
        print("Starting fresh with a weak prompt (strict string comparison).")
    else:
        print(f"Continuing from generation {gen_start} (run --reset to start over).")
    print()

    before = await evaluate(gen_start)
    await improve()
    after = await evaluate(gen_start + 1)

    print("\n========================================")
    print("           RESULTS SUMMARY")
    print("========================================")
    print(f"  Generation {gen_start}:     {before['score']:.2f}")
    print(f"  Generation {gen_start + 1}:     {after['score']:.2f}")
    delta = after["score"] - before["score"]
    if delta > 0:
        print(f"  Improvement:      +{delta * 100:.0f}%")
    elif delta == 0:
        print("  No change")
    else:
        print(f"  Regression:       {delta * 100:.0f}%")
    print("========================================")
    print(f"\nFiles the MetaAgent can edit:")
    print(f"  {PROMPT_FILE}  (the grading prompt)")
    print(f"  {os.path.join(EXAMPLE_DIR, 'run.py')}  (this script)")
    print(f"  {os.path.join(EXAMPLE_DIR, 'domain.py')}  (evaluation logic)")
    print(f"  {os.path.join(EXAMPLE_DIR, 'tasks.json')}  (task definitions)")
    print(f"\nRun again to keep improving. Use --reset to start over.\n")


if __name__ == "__main__":
    asyncio.run(main())
