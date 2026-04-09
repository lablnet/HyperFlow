"""Bash tool: run shell commands.

@since v1.0.0
@author Muhammad Umer Farooq <umer@lablnet.com>
"""

from __future__ import annotations

import subprocess

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field


class BashInput(BaseModel):
    command: str = Field(description="The bash command to run.")


def create_bash_tool(timeout: int = 120) -> StructuredTool:
    """Create a new Bash tool.

    Args:
        timeout: Timeout in seconds (default 120).

    Returns:
        The Bash StructuredTool.

    @since v1.0.0
    @author Muhammad Umer Farooq <umer@lablnet.com>
    """

    def _run_bash(command: str) -> str:
        try:
            result = subprocess.run(
                command,
                shell=True,
                executable="/bin/bash",
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            output = result.stdout.strip()
            return output or "(no output)"
        except subprocess.TimeoutExpired:
            return f"Command timed out after {timeout} seconds"
        except Exception as e:
            stdout = getattr(e, "stdout", "") or ""
            stderr = getattr(e, "stderr", "") or ""
            stdout = stdout.strip() if isinstance(stdout, str) else ""
            stderr = stderr.strip() if isinstance(stderr, str) else ""
            parts: list[str] = []
            if stdout:
                parts.append(stdout)
            if stderr:
                parts.append("Error:\n" + stderr)
            return "\n".join(parts) if parts else f"Command failed with error: {e}"

    return StructuredTool.from_function(
        func=_run_bash,
        name="bash",
        description=(
            "Run commands in a bash shell. State is NOT persistent across calls. "
            "Avoid commands that produce very large output. "
            "Run long-lived commands in the background with &."
        ),
        args_schema=BashInput,
    )
