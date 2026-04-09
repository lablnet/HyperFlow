"""A buggy calculator tool.

Has several intentional bugs that cause wrong answers:
- Multiplication is broken for numbers > 10 (returns a + b instead of a * b)
- Subtraction always returns absolute value (never negative)
- Division truncates to integer (loses decimals)
The MetaAgent's job is to find and fix these bugs.

@since v1.0.0
@author Muhammad Umer Farooq <umer@lablnet.com>
"""
from __future__ import annotations

import math
import re

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field


class CalcInput(BaseModel):
    expression: str = Field(description="A simple math expression: 'a op b' where op is +, -, *, /")


def _evaluate_expression(expr: str) -> float:
    cleaned = re.sub(r"\s+", "", expr)
    match = re.match(r"^(-?\d+\.?\d*)([\+\-\*\/])(-?\d+\.?\d*)$", cleaned)
    if not match:
        raise ValueError(f"Cannot parse: {expr}")

    a = float(match.group(1))
    op = match.group(2)
    b = float(match.group(3))

    if op == "+":
        return a + b
    elif op == "-":
        # BUG: always returns absolute value, never negative
        return abs(a - b)
    elif op == "*":
        # BUG: for numbers > 10, returns sum instead of product
        if a > 10 or b > 10:
            return a + b
        return a * b
    elif op == "/":
        if b == 0:
            raise ValueError("Division by zero")
        # BUG: truncates to integer
        return math.floor(a / b)
    else:
        raise ValueError(f"Unknown operator: {op}")


def create_calc_tool() -> StructuredTool:
    """Create the buggy calculator tool."""

    def _run_calc(expression: str) -> str:
        try:
            result = _evaluate_expression(expression)
            return str(result)
        except Exception as err:
            return f"Error: {err}"

    return StructuredTool.from_function(
        func=_run_calc,
        name="calculator",
        description=(
            "Calculate math. You MUST use this tool for ALL math -- do not compute in your head. "
            "Pass a simple expression like '2 + 3', '10 * 5', '7 - 3', '15 / 4'."
        ),
        args_schema=CalcInput,
    )
