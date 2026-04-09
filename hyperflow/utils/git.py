"""Git operations: patch, reset, diff.

@since v1.0.0
@author Muhammad Umer Farooq <umer@lablnet.com>
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from git import Repo


@dataclass
class GitOps:
    """Wrapper around a git repository."""

    repo: Repo
    repo_path: str


def create_git_ops(repo_path: str) -> GitOps:
    """Create a new GitOps object.

    Args:
        repo_path: The path of the repository.

    Returns:
        The GitOps object.

    @since v1.0.0
    @author Muhammad Umer Farooq <umer@lablnet.com>
    """
    return GitOps(repo=Repo(repo_path), repo_path=repo_path)


def apply_patch(ops: GitOps, patch_file: str) -> None:
    """Apply a diff/patch file to the repository.

    Args:
        ops: The GitOps object.
        patch_file: The path of the patch file.

    @since v1.0.0
    @author Muhammad Umer Farooq <umer@lablnet.com>
    """
    if not os.path.exists(patch_file):
        raise FileNotFoundError(f"Patch file not found: {patch_file}")
    ops.repo.git.apply("--allow-empty", patch_file)


def apply_patches(ops: GitOps, patch_files: list[str]) -> None:
    """Apply multiple patch files in order.

    Args:
        ops: The GitOps object.
        patch_files: The paths of the patch files.

    @since v1.0.0
    @author Muhammad Umer Farooq <umer@lablnet.com>
    """
    for patch in patch_files:
        apply_patch(ops, patch)


def diff_versus_commit(ops: GitOps, base_commit: str) -> str:
    """Get the diff between the current state and a base commit.

    Args:
        ops: The GitOps object.
        base_commit: The commit to diff against.

    Returns:
        The diff string.

    @since v1.0.0
    @author Muhammad Umer Farooq <umer@lablnet.com>
    """
    return ops.repo.git.diff(base_commit)


def reset_paths_to_commit(ops: GitOps, commit: str, paths: list[str]) -> None:
    """Reset specific paths to a given commit.

    Args:
        ops: The GitOps object.
        commit: The commit to reset to.
        paths: The paths to reset.

    @since v1.0.0
    @author Muhammad Umer Farooq <umer@lablnet.com>
    """
    ops.repo.git.checkout(commit, "--", *paths)


def hard_reset(ops: GitOps, commit: str) -> None:
    """Hard reset the repo to a commit.

    Args:
        ops: The GitOps object.
        commit: The commit to reset to.

    @since v1.0.0
    @author Muhammad Umer Farooq <umer@lablnet.com>
    """
    ops.repo.git.reset("--hard", commit)
    ops.repo.git.clean("-f", "-d")


def get_head_commit(ops: GitOps) -> str:
    """Get the current HEAD commit hash.

    Args:
        ops: The GitOps object.

    Returns:
        The current HEAD commit hash.

    @since v1.0.0
    @author Muhammad Umer Farooq <umer@lablnet.com>
    """
    try:
        return str(ops.repo.head.commit.hexsha)
    except Exception:
        return "HEAD"
