"""Common utility functions.

@since v1.0.0
@author Muhammad Umer Farooq <umer@lablnet.com>
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


def extract_jsons(text: str) -> list[dict[str, Any]]:
    """Extract JSON objects from a string that may contain mixed text and JSON.
    Handles nested braces correctly.

    Args:
        text: The text to extract JSON objects from.

    Returns:
        The extracted JSON objects.

    @since v1.0.0
    @author Muhammad Umer Farooq <umer@lablnet.com>
    """
    results: list[dict[str, Any]] = []
    depth = 0
    start = -1

    for i, ch in enumerate(text):
        if ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0 and start != -1:
                try:
                    parsed = json.loads(text[start : i + 1])
                    if isinstance(parsed, dict):
                        results.append(parsed)
                except (json.JSONDecodeError, ValueError):
                    pass  # not valid JSON, skip
                start = -1

    return results


def file_exists_and_not_empty(file_path: str | Path) -> bool:
    """Check if a file exists and is not empty.

    Args:
        file_path: The path of the file.

    Returns:
        True if the file exists and is not empty, False otherwise.

    @since v1.0.0
    @author Muhammad Umer Farooq <umer@lablnet.com>
    """
    try:
        p = Path(file_path)
        return p.is_file() and p.stat().st_size > 0
    except OSError:
        return False


def load_json_file(file_path: str | Path) -> Any:
    """Load a JSON file.

    Args:
        file_path: The path of the JSON file.

    Returns:
        The parsed JSON object.

    @since v1.0.0
    @author Muhammad Umer Farooq <umer@lablnet.com>
    """
    return json.loads(Path(file_path).read_text(encoding="utf-8"))


def ensure_dir(dir_path: str | Path) -> None:
    """Ensure a directory exists.

    Args:
        dir_path: The path of the directory.

    @since v1.0.0
    @author Muhammad Umer Farooq <umer@lablnet.com>
    """
    Path(dir_path).mkdir(parents=True, exist_ok=True)


def gen_output_dir(output_dir: str, gen_id: str | int) -> str:
    """Generate the output directory for a specific generation.

    Args:
        output_dir: The path of the output directory.
        gen_id: The ID of the generation.

    Returns:
        The path of the output directory.

    @since v1.0.0
    @author Muhammad Umer Farooq <umer@lablnet.com>
    """
    return os.path.join(output_dir, f"gen_{gen_id}")
