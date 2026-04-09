"""File viewing and editing tool.

@since v1.0.0
@author Muhammad Umer Farooq <umer@lablnet.com>
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Optional

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

# The history of file edits.
_file_history: dict[str, list[str]] = {}


def _truncate(content: str, max_len: int = 10000) -> str:
    """Truncate the content of the file.

    Args:
        content: The content of the file.
        max_len: The maximum length of the content.

    Returns:
        The truncated content.

    @since v1.0.0
    @author Muhammad Umer Farooq <umer@lablnet.com>
    """
    if len(content) <= max_len:
        return content
    half = max_len // 2
    return content[:half] + "\n<response clipped>\n" + content[-half:]


def _format_with_line_numbers(content: str, file_path: str, start_line: int = 1) -> str:
    """Format the content of the file with line numbers.

    Args:
        content: The content of the file.
        file_path: The path of the file.
        start_line: The starting line number.

    Returns:
        The formatted content.

    @since v1.0.0
    @author Muhammad Umer Farooq <umer@lablnet.com>
    """
    numbered = "\n".join(f"{str(i + start_line).rjust(6)}\t{line}" for i, line in enumerate(content.split("\n")))
    return f"Result of cat -n on {file_path}:\n{numbered}\n"


def _view_file(file_path: str, view_range: Optional[list[int]] = None) -> str:
    """View the content of the file.

    Args:
        file_path: The path of the file.
        view_range: The range of the lines to view.

    Returns:
        The content of the file.

    @since v1.0.0
    @author Muhammad Umer Farooq <umer@lablnet.com>
    """
    if os.path.isdir(file_path):
        try:
            result = subprocess.run(
                ["find", file_path, "-maxdepth", "2", "-not", "-path", "*/.*"],
                capture_output=True,
                text=True,
            )
            return f"Files in {file_path}:\n{_truncate(result.stdout, 5000)}"
        except Exception:
            return f"Error listing directory {file_path}"

    content = Path(file_path).read_text(encoding="utf-8")

    if not view_range:
        return _format_with_line_numbers(_truncate(content), file_path)

    lines = content.split("\n")
    start, end = view_range[0], view_range[1]
    sliced = lines[start - 1 : None if end == -1 else end]
    return _format_with_line_numbers("\n".join(sliced), file_path, start)


def _replace_text(file_path: str, old_str: str, new_str: str) -> str:
    """Replace the text in the file.

    Args:
        file_path: The path of the file.
        old_str: The old text to replace.
        new_str: The new text to replace with.

    Returns:
        The result message.

    @since v1.0.0
    @author Muhammad Umer Farooq <umer@lablnet.com>
    """
    content = Path(file_path).read_text(encoding="utf-8")
    count = content.count(old_str)

    if count == 0:
        return f"Error: old_str not found in {file_path}."
    if count > 1:
        return f"Error: old_str appears {count} times. Make it unique."

    history = _file_history.setdefault(file_path, [])
    history.append(content)

    new_content = content.replace(old_str, new_str, 1)
    Path(file_path).write_text(new_content, encoding="utf-8")

    replace_line = content.split(old_str)[0].count("\n")
    start = max(0, replace_line - 3)
    end = replace_line + 4 + new_str.count("\n")
    snippet = "\n".join(new_content.split("\n")[start:end])

    return f"File {file_path} edited. {_format_with_line_numbers(snippet, file_path, start + 1)}"


def _insert_text(file_path: str, insert_line: int, new_str: str) -> str:
    """Insert the text into the file.

    Args:
        file_path: The path of the file.
        insert_line: The line number to insert the text at.
        new_str: The text to insert.

    Returns:
        The result message.

    @since v1.0.0
    @author Muhammad Umer Farooq <umer@lablnet.com>
    """
    content = Path(file_path).read_text(encoding="utf-8")
    lines = content.split("\n")

    if insert_line < 0 or insert_line > len(lines):
        return f"Error: insert_line {insert_line} out of range [0, {len(lines)}]."

    history = _file_history.setdefault(file_path, [])
    history.append(content)

    new_lines = lines[:insert_line] + new_str.split("\n") + lines[insert_line:]
    Path(file_path).write_text("\n".join(new_lines), encoding="utf-8")

    return f"File {file_path} edited. Inserted at line {insert_line}."


def _undo_edit(file_path: str) -> str:
    """Undo the last edit to the file.

    Args:
        file_path: The path of the file.

    Returns:
        The result message.

    @since v1.0.0
    @author Muhammad Umer Farooq <umer@lablnet.com>
    """
    history = _file_history.get(file_path)
    if not history:
        return f"No edit history for {file_path}."

    prev = history.pop()
    Path(file_path).write_text(prev, encoding="utf-8")
    return f"Reverted last edit to {file_path}."


class EditorInput(BaseModel):
    command: str = Field(description="The operation to perform: view, create, str_replace, insert, undo_edit.")
    path: str = Field(description="Absolute path to file or directory.")
    file_text: Optional[str] = Field(default=None, description="Content for create command.")
    old_str: Optional[str] = Field(default=None, description="String to find for str_replace.")
    new_str: Optional[str] = Field(default=None, description="Replacement string for str_replace or insert.")
    insert_line: Optional[int] = Field(
        default=None, description="Line number for insert (0-indexed, inserts after this line)."
    )
    view_range: Optional[list[int]] = Field(
        default=None, description="Line range [start, end] for view (1-indexed, use -1 for end of file)."
    )


def create_editor_tool(timeout: int = 120) -> StructuredTool:
    """Create a new Editor tool.

    Args:
        timeout: Timeout in seconds (default 120).

    Returns:
        The Editor StructuredTool.

    @since v1.0.0
    @author Muhammad Umer Farooq <umer@lablnet.com>
    """

    def _run_editor(
        command: str,
        path: str,
        file_text: Optional[str] = None,
        old_str: Optional[str] = None,
        new_str: Optional[str] = None,
        insert_line: Optional[int] = None,
        view_range: Optional[list[int]] = None,
    ) -> str:
        try:
            if command == "view":
                return _view_file(path, view_range)
            if command == "create":
                if not file_text:
                    return "Error: file_text is required for create."
                if os.path.exists(path):
                    return f"Error: File already exists at {path}. Use str_replace to edit."
                os.makedirs(os.path.dirname(path), exist_ok=True)
                Path(path).write_text(file_text, encoding="utf-8")
                return f"File created at: {path}"
            if command == "str_replace":
                if not old_str:
                    return "Error: old_str is required for str_replace."
                return _replace_text(path, old_str, new_str or "")
            if command == "insert":
                if insert_line is None:
                    return "Error: insert_line is required for insert."
                if new_str is None:
                    return "Error: new_str is required for insert."
                return _insert_text(path, insert_line, new_str)
            if command == "undo_edit":
                return _undo_edit(path)
            return f"Error: Unknown command {command}"
        except Exception as err:
            return f"Error: {err}"

    return StructuredTool.from_function(
        func=_run_editor,
        name="editor",
        description=(
            "File viewing and editing tool. Commands: view, create, str_replace, insert, undo_edit. "
            "For str_replace, old_str must match EXACTLY and be unique in the file."
        ),
        args_schema=EditorInput,
    )
