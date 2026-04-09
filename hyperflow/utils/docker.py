"""Dockerode wrapper for containers.

@since v1.0.0
@author Muhammad Umer Farooq <umer@lablnet.com>
"""

from __future__ import annotations

import os
import subprocess
import tempfile
from dataclasses import dataclass, field
from typing import Any

import docker as docker_sdk


@dataclass
class DockerConfig:
    """Configuration for a Docker container."""

    image_name: str
    root_dir: str
    env: dict[str, str] = field(default_factory=dict)


class DockerManager:
    """Manages Docker containers for execution."""

    def __init__(self) -> None:
        self.client = docker_sdk.from_env()

    def build_image(self, context_dir: str, image_name: str) -> None:
        """Build a Docker image from a directory containing a Dockerfile.

        Args:
            context_dir: The path of the context directory.
            image_name: The name of the image.

        @since v1.0.0
        @author Muhammad Umer Farooq <umer@lablnet.com>
        """
        self.client.images.build(path=context_dir, tag=image_name, rm=True)

    def create_container(self, config: DockerConfig, container_name: str) -> Any:
        """Create and start a container.

        Args:
            config: The configuration of the container.
            container_name: The name of the container.

        Returns:
            The container object.

        @since v1.0.0
        @author Muhammad Umer Farooq <umer@lablnet.com>
        """
        env_list = [f"{k}={v}" for k, v in config.env.items()] if config.env else []
        abs_root = os.path.abspath(config.root_dir)
        mount_target = f"/{os.path.basename(config.root_dir)}"

        container = self.client.containers.create(
            image=config.image_name,
            name=container_name,
            environment=env_list,
            volumes={abs_root: {"bind": mount_target, "mode": "rw"}},
            command=["tail", "-f", "/dev/null"],
            detach=True,
        )
        container.start()
        return container

    def exec(
        self,
        container: Any,
        command: list[str],
        workdir: str | None = None,
    ) -> dict[str, Any]:
        """Execute a command inside a running container.

        Args:
            container: The container to execute the command in.
            command: The command to execute.
            workdir: The working directory to execute the command in.

        Returns:
            Dict with ``exitCode`` (int) and ``output`` (str).

        @since v1.0.0
        @author Muhammad Umer Farooq <umer@lablnet.com>
        """
        kwargs: dict[str, Any] = {"cmd": command, "stdout": True, "stderr": True, "demux": True}
        if workdir:
            kwargs["workdir"] = workdir

        exit_code, (stdout_data, stderr_data) = container.exec_run(**kwargs)
        stdout_str = (stdout_data or b"").decode("utf-8", errors="replace")
        stderr_str = (stderr_data or b"").decode("utf-8", errors="replace")
        output = stdout_str + stderr_str

        return {"exitCode": exit_code, "output": output}

    def copy_to_container(self, container: Any, source_path: str, dest_path: str) -> None:
        """Copy a file from the host into a container.

        Args:
            container: The container to copy the file to.
            source_path: The path of the file to copy from the host.
            dest_path: The path of the file to copy to the container.

        @since v1.0.0
        @author Muhammad Umer Farooq <umer@lablnet.com>
        """
        tmp_tar = os.path.join(tempfile.gettempdir(), f"hyperflow-copy-{os.getpid()}.tar")
        try:
            source_dir = os.path.dirname(source_path)
            source_file = os.path.basename(source_path)
            subprocess.run(
                ["tar", "cf", tmp_tar, "-C", source_dir, source_file],
                check=True,
                capture_output=True,
            )
            with open(tmp_tar, "rb") as tar_f:
                container.put_archive(os.path.dirname(dest_path), tar_f.read())
        finally:
            if os.path.exists(tmp_tar):
                os.unlink(tmp_tar)

    def copy_from_container(self, container: Any, source_path: str, dest_path: str) -> None:
        """Copy a file from a container to the host.

        Args:
            container: The container to copy the file from.
            source_path: The path of the file to copy from the container.
            dest_path: The path of the file to copy to the host.

        @since v1.0.0
        @author Muhammad Umer Farooq <umer@lablnet.com>
        """
        tmp_tar = os.path.join(tempfile.gettempdir(), f"hyperflow-get-{os.getpid()}.tar")
        try:
            bits, _stat = container.get_archive(source_path)
            with open(tmp_tar, "wb") as f:
                for chunk in bits:
                    f.write(chunk)

            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            subprocess.run(
                ["tar", "xf", tmp_tar, "-C", os.path.dirname(dest_path)],
                check=True,
                capture_output=True,
            )
        finally:
            if os.path.exists(tmp_tar):
                os.unlink(tmp_tar)

    def cleanup(self, container: Any) -> None:
        """Stop and remove a container.

        Args:
            container: The container to stop and remove.

        @since v1.0.0
        @author Muhammad Umer Farooq <umer@lablnet.com>
        """
        try:
            container.stop()
        except Exception:
            pass  # already stopped
        try:
            container.remove()
        except Exception:
            pass  # already removed
