"""HyperFlow Calculator Example: Tool Improvement Demo.

The TaskAgent has a BUGGY calculator tool (wrong answers!).
The MetaAgent will edit calc_tool.py to fix the bugs.

@since v1.0.0
@author Muhammad Umer Farooq <umer@lablnet.com>
"""
from __future__ import annotations

import asyncio
import importlib
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
TOOL_FILE = os.path.join(EXAMPLE_DIR, "calc_tool.py")
TOOL_BACKUP = os.path.join(EXAMPLE_DIR, "calc_tool_original.py")
EVAL_DIR = os.path.abspath("./outputs/calculator_eval")


def load_tasks() -> list[dict]:
    return json.loads(Path(os.path.join(EXAMPLE_DIR, "tasks.json")).read_text(encoding="utf-8"))


def reset_tool() -> None:
    shutil.copyfile(TOOL_BACKUP, TOOL_FILE)


async def evaluate(generation: int) -> dict:
    model = os.environ.get("HYPERFLOW_MODEL", "openai/gpt-4o")
    llm = create_llm(LLMConfig(model=model, temperature=0))

    # Dynamically reload the calc tool module
    import calc_tool
    importlib.reload(calc_tool)
    calc_tool_instance = calc_tool.create_calc_tool()

    print(f"\n--- Generation {generation} ---")

    tasks = load_tasks()
    details: list[str] = []
    correct = 0

    for task in tasks:
        user_message = (
            "You MUST use the calculator tool for this math problem. Do NOT compute the answer yourself.\n"
            "Call the calculator tool, then return exactly what it gives you.\n\n"
            f"Problem: {task['description']}\n\n"
            'Respond with ONLY JSON: {{ "response": "<the number the calculator returned>" }}'
        )

        result = await chat_with_agent(
            user_message,
            ChatWithAgentOptions(
                llm=llm,
                tools=[calc_tool_instance],
                log=lambda *a: None,
            ),
        )

        prediction = "error"
        try:
            extracted = extract_jsons(result.response)
            if extracted and "response" in extracted[-1]:
                prediction = str(extracted[-1]["response"]).strip()
        except Exception:
            import re
            num_match = re.search(r"-?\d+\.?\d*", result.response)
            if num_match:
                prediction = num_match.group(0)

        is_correct = prediction == task["expected"] or (
            _safe_float(prediction) == _safe_float(task["expected"])
        )
        if is_correct:
            correct += 1

        icon = "PASS" if is_correct else "FAIL"
        line = f'  [{icon}] {task["id"]}: "{task["description"]}" -> {prediction} (expected: {task["expected"]})'
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
            f"Calculator tool source code ({TOOL_FILE}):",
            Path(TOOL_FILE).read_text(encoding="utf-8"),
            "",
            "All results:",
            *details,
            "",
            "FAILURES -- the calculator tool returned wrong answers for these:",
            *[d for d in details if "[FAIL]" in d],
            "",
            f"FIX THE BUGS in {TOOL_FILE}. The _evaluate_expression function has bugs:",
            "- Subtraction returns abs() instead of allowing negatives",
            "- Multiplication returns a+b instead of a*b when numbers > 10",
            "- Division uses math.floor() which truncates decimals",
            "Edit the function to fix these bugs.",
        ]),
        encoding="utf-8",
    )

    return {"score": score, "details": details}


def _safe_float(val: str) -> float | None:
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


async def improve() -> None:
    model = os.environ.get("HYPERFLOW_MODEL", "openai/gpt-4o")

    print("=== MetaAgent analyzing failures and fixing the tool ===\n")

    eval_results_target = os.path.join(EXAMPLE_DIR, "eval_results")
    ensure_dir(eval_results_target)
    if os.path.exists(EVAL_DIR):
        shutil.copytree(EVAL_DIR, eval_results_target, dirs_exist_ok=True)

    meta_agent = MetaAgent(AgentOptions(model=model))

    await meta_agent.forward(
        MetaAgentPromptOptions(
            repo_path=EXAMPLE_DIR,
            eval_path=EXAMPLE_DIR,
            iterations_left=1,
        )
    )

    shutil.rmtree(eval_results_target, ignore_errors=True)

    print("\nMetaAgent finished editing.\n")
    print("Updated tool code:")
    code = Path(TOOL_FILE).read_text(encoding="utf-8")
    for line in code.splitlines():
        print(f"  {line}")


def get_generation_count() -> int:
    if not os.path.exists(EVAL_DIR):
        return 0
    return len([d for d in os.listdir(EVAL_DIR) if d.startswith("gen_")])


async def main() -> None:
    force_reset = "--reset" in sys.argv

    if force_reset:
        shutil.rmtree(EVAL_DIR, ignore_errors=True)
        reset_tool()
        print("Reset to original buggy calculator tool.\n")

    gen_start = get_generation_count()

    print("=== HyperFlow: Tool Improvement Demo (Calculator) ===")
    print("The TaskAgent has a BUGGY calculator tool (wrong answers!).")
    print("The MetaAgent will edit calc_tool.py to fix the bugs.")
    if gen_start > 0:
        print(f"Continuing from generation {gen_start} (run --reset to start over).")

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
    print(f"\nTool source: {TOOL_FILE}")
    print("Run again to keep improving. Use --reset to start over.\n")


if __name__ == "__main__":
    asyncio.run(main())
