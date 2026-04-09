"""Execution strategy: local subprocess vs Docker container.

Abstracts whether generations run locally or inside Docker containers.

@since v1.0.0
@author Muhammad Umer Farooq <umer@lablnet.com>
"""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import time
from abc import ABC, abstractmethod
from typing import Any

from .docker import DockerConfig, DockerManager
from .git import GitOps, apply_patches, create_git_ops, hard_reset


class Executor(ABC):
    """Execution strategy interface.
    Abstracts whether generations run locally or inside Docker containers.
    """

    @abstractmethod
    def setup(self, patch_files: list[str]) -> None: ...

    @abstractmethod
    def run(self, command: str, workdir: str | None = None) -> dict[str, Any]: ...

    @abstractmethod
    def copy_in(self, src: str, dest: str) -> None: ...

    @abstractmethod
    def copy_out(self, src: str, dest: str) -> None: ...

    @abstractmethod
    def diff(self) -> str: ...

    @abstractmethod
    def get_workdir(self) -> str: ...

    @abstractmethod
    def cleanup(self) -> None: ...


class LocalExecutor(Executor):
    """LocalExecutor -- runs generations in a temporary directory.
    Fast for development and testing. No sandboxing.
    """

    def __init__(self, repo_path: str, base_commit: str = "HEAD") -> None:
        """Create a new LocalExecutor.

        Args:
            repo_path: The path of the repository.
            base_commit: The commit to reset to.

        @since v1.0.0
        @author Muhammad Umer Farooq <umer@lablnet.com>
        """
        self._repo_path = repo_path
        self._base_commit = base_commit
        self._workdir = tempfile.mkdtemp(prefix="hyperflow-")
        self._git_ops: GitOps | None = None

    def setup(self, patch_files: list[str]) -> None:
        """Setup the LocalExecutor.

        Args:
            patch_files: The paths of the patch files.

        @since v1.0.0
        @author Muhammad Umer Farooq <umer@lablnet.com>
        """
        subprocess.run(
            ["cp", "-r", f"{self._repo_path}/.", f"{self._workdir}/"],
            check=True,
            capture_output=True,
        )

        if os.path.exists(os.path.join(self._workdir, ".git")):
            self._git_ops = create_git_ops(self._workdir)
            if patch_files:
                apply_patches(self._git_ops, patch_files)
        elif patch_files:
            print("[LocalExecutor] No .git directory found; skipping patch application")

    def run(self, command: str, workdir: str | None = None) -> dict[str, Any]:
        """Run a command in the LocalExecutor.

        Args:
            command: The command to run.
            workdir: The working directory to run the command in.

        Returns:
            Dict with ``exitCode`` (int) and ``output`` (str).

        @since v1.0.0
        @author Muhammad Umer Farooq <umer@lablnet.com>
        """
        cwd = workdir or self._workdir
        try:
            result = subprocess.run(
                command,
                cwd=cwd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=6 * 60 * 60,  # 6 hours
            )
            return {"exitCode": result.returncode, "output": result.stdout + result.stderr}
        except subprocess.TimeoutExpired as e:
            return {"exitCode": 1, "output": f"Timeout: {e}"}
        except Exception as e:
            return {"exitCode": 1, "output": str(e)}

    def copy_in(self, src: str, dest: str) -> None:
        """Copy a file into the LocalExecutor.

        Args:
            src: The path of the file to copy.
            dest: The path of the file to copy to.

        @since v1.0.0
        @author Muhammad Umer Farooq <umer@lablnet.com>
        """
        full_dest = dest if os.path.isabs(dest) else os.path.join(self._workdir, dest)
        os.makedirs(os.path.dirname(full_dest), exist_ok=True)
        subprocess.run(["cp", "-r", src, full_dest], check=True, capture_output=True)

    def copy_out(self, src: str, dest: str) -> None:
        """Copy a file out of the LocalExecutor.

        Args:
            src: The path of the file to copy.
            dest: The path of the file to copy to.

        @since v1.0.0
        @author Muhammad Umer Farooq <umer@lablnet.com>
        """
        full_src = src if os.path.isabs(src) else os.path.join(self._workdir, src)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        subprocess.run(["cp", "-r", full_src, dest], check=True, capture_output=True)

    def get_workdir(self) -> str:
        """Get the working directory of the LocalExecutor.

        Returns:
            The working directory.

        @since v1.0.0
        @author Muhammad Umer Farooq <umer@lablnet.com>
        """
        return self._workdir

    def diff(self) -> str:
        if self._git_ops:
            return self._git_ops.repo.git.diff()
        return ""

    def cleanup(self) -> None:
        if self._git_ops:
            try:
                hard_reset(self._git_ops, self._base_commit)
            except Exception:
                pass  # best effort
        try:
            shutil.rmtree(self._workdir, ignore_errors=True)
        except Exception:
            pass  # best effort


class DockerExecutor(Executor):
    """DockerExecutor -- runs generations inside Docker containers.
    Safe for untrusted LLM-generated code.
    """

    def __init__(
        self,
        config: DockerConfig,
        container_name: str,
    ) -> None:
        """Create a new DockerExecutor.

        Args:
            config: The configuration of the DockerExecutor.
            container_name: The name of the container.

        @since v1.0.0
        @author Muhammad Umer Farooq <umer@lablnet.com>
        """
        self._config = config
        self._container_name = container_name
        self._docker = DockerManager()
        self._container: Any = None
        self._container_workdir = f"/{os.path.basename(config.root_dir)}"

    def setup(self, patch_files: list[str]) -> None:
        """Setup the DockerExecutor.

        Args:
            patch_files: The paths of the patch files.

        @since v1.0.0
        @author Muhammad Umer Farooq <umer@lablnet.com>
        """
        self._container = self._docker.create_container(self._config, self._container_name)

        if patch_files:
            for patch in patch_files:
                self._docker.copy_to_container(self._container, patch, f"/tmp/{os.path.basename(patch)}")
                self._docker.exec(
                    self._container,
                    ["git", "apply", "--allow-empty", f"/tmp/{os.path.basename(patch)}"],
                    self._container_workdir,
                )

    def run(self, command: str, workdir: str | None = None) -> dict[str, Any]:
        """Run a command in the DockerExecutor.

        Args:
            command: The command to run.
            workdir: The working directory to run the command in.

        Returns:
            Dict with ``exitCode`` (int) and ``output`` (str).

        @since v1.0.0
        @author Muhammad Umer Farooq <umer@lablnet.com>
        """
        if not self._container:
            raise RuntimeError("Container not initialized. Call setup() first.")
        return self._docker.exec(
            self._container,
            ["bash", "-lc", command],
            workdir or self._container_workdir,
        )

    def copy_in(self, src: str, dest: str) -> None:
        """Copy a file into the DockerExecutor.

        Args:
            src: The path of the file to copy.
            dest: The path of the file to copy to.

        @since v1.0.0
        @author Muhammad Umer Farooq <umer@lablnet.com>
        """
        if not self._container:
            raise RuntimeError("Container not initialized.")
        self._docker.copy_to_container(self._container, src, dest)

    def copy_out(self, src: str, dest: str) -> None:
        """Copy a file out of the DockerExecutor.

        Args:
            src: The path of the file to copy.
            dest: The path of the file to copy to.

        @since v1.0.0
        @author Muhammad Umer Farooq <umer@lablnet.com>
        """
        if not self._container:
            raise RuntimeError("Container not initialized.")
        self._docker.copy_from_container(self._container, src, dest)

    def get_workdir(self) -> str:
        """Get the working directory of the DockerExecutor.

        Returns:
            The working directory.

        @since v1.0.0
        @author Muhammad Umer Farooq <umer@lablnet.com>
        """
        return self._container_workdir

    def diff(self) -> str:
        if not self._container:
            return ""
        result = self._docker.exec(self._container, ["git", "diff"], self._container_workdir)
        return result["output"]

    def cleanup(self) -> None:
        if self._container:
            self._docker.cleanup(self._container)
            self._container = None


def create_executor(
    mode: str,
    options: dict[str, Any],
) -> Executor:
    """Create a new Executor.

    Args:
        mode: The mode of the Executor (``"local"`` or ``"docker"``).
        options: The options for the Executor. Keys:
            - ``repoPath`` (str): Path to the repository.
            - ``baseCommit`` (str, optional): Base commit hash.
            - ``imageName`` (str, optional): Docker image name.
            - ``containerName`` (str, optional): Docker container name.
            - ``env`` (dict, optional): Environment variables.

    Returns:
        The Executor instance.

    @since v1.0.0
    @author Muhammad Umer Farooq <umer@lablnet.com>
    """
    if mode == "docker":
        return DockerExecutor(
            config=DockerConfig(
                image_name=options.get("imageName", "hyperflow"),
                root_dir=options["repoPath"],
                env=options.get("env", {}),
            ),
            container_name=options.get("containerName", f"hyperflow-{int(time.time() * 1000)}"),
        )

    return LocalExecutor(options["repoPath"], options.get("baseCommit", "HEAD"))
