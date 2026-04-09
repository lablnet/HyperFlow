"""JSONL archive CRUD, scores, lineage patches.

@since v1.0.0
@author Muhammad Umer Farooq <umer@lablnet.com>
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .constants import ARCHIVE_FILENAME, METADATA_FILENAME


@dataclass
class ArchiveEntry:
    """A single generation entry in the archive."""

    gen_id: str | int
    parent_id: str | int | None
    patch_files: list[str]
    scores: dict[str, float]
    metadata: dict[str, Any]
    valid_parent: bool
    timestamp: str


@dataclass
class ArchiveData:
    """The full archive state: ordered gen ids + entries map."""

    archive: list[str | int] = field(default_factory=list)
    entries: dict[str, ArchiveEntry] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Serialization helpers (camelCase keys for binary-compatible JSONL format)
# ---------------------------------------------------------------------------


def _archive_entry_to_dict(entry: ArchiveEntry) -> dict[str, Any]:
    return {
        "genId": entry.gen_id,
        "parentId": entry.parent_id,
        "patchFiles": entry.patch_files,
        "scores": entry.scores,
        "metadata": entry.metadata,
        "validParent": entry.valid_parent,
        "timestamp": entry.timestamp,
    }


def _dict_to_archive_entry(d: dict[str, Any]) -> ArchiveEntry:
    return ArchiveEntry(
        gen_id=d["genId"],
        parent_id=d.get("parentId"),
        patch_files=d.get("patchFiles", []),
        scores=d.get("scores", {}),
        metadata=d.get("metadata", {}),
        valid_parent=d.get("validParent", True),
        timestamp=d.get("timestamp", ""),
    )


def _archive_data_to_dict(data: ArchiveData) -> dict[str, Any]:
    return {
        "archive": data.archive,
        "entries": {k: _archive_entry_to_dict(v) for k, v in data.entries.items()},
    }


def _dict_to_archive_data(d: dict[str, Any]) -> ArchiveData:
    return ArchiveData(
        archive=d.get("archive", []),
        entries={k: _dict_to_archive_entry(v) for k, v in d.get("entries", {}).items()},
    )


# ---------------------------------------------------------------------------
# Archive persistence
# ---------------------------------------------------------------------------


def load_archive(output_dir: str) -> ArchiveData:
    """Load the archive from a JSONL file.
    Each line is a JSON object representing a snapshot of the archive state.

    Args:
        output_dir: The path of the output directory.

    Returns:
        The archive data.

    @since v1.0.0
    @author Muhammad Umer Farooq <umer@lablnet.com>
    """
    archive_path = os.path.join(output_dir, ARCHIVE_FILENAME)

    if not os.path.exists(archive_path):
        return ArchiveData()

    text = Path(archive_path).read_text(encoding="utf-8").strip()
    lines = [line for line in text.split("\n") if line.strip()]

    if not lines:
        return ArchiveData()

    return _dict_to_archive_data(json.loads(lines[-1]))


def save_archive(output_dir: str, data: ArchiveData) -> None:
    """Append a new archive snapshot to the JSONL file.

    Args:
        output_dir: The path of the output directory.
        data: The archive data to save.

    @since v1.0.0
    @author Muhammad Umer Farooq <umer@lablnet.com>
    """
    archive_path = os.path.join(output_dir, ARCHIVE_FILENAME)
    with open(archive_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(_archive_data_to_dict(data)) + "\n")


def update_archive(
    output_dir: str,
    current_archive: ArchiveData,
    new_entry: ArchiveEntry,
) -> ArchiveData:
    """Add a new generation to the archive and persist.

    Args:
        output_dir: The path of the output directory.
        current_archive: The current archive data.
        new_entry: The new entry to add to the archive.

    Returns:
        The updated archive data.

    @since v1.0.0
    @author Muhammad Umer Farooq <umer@lablnet.com>
    """
    updated = ArchiveData(
        archive=[*current_archive.archive, new_entry.gen_id],
        entries={**current_archive.entries, str(new_entry.gen_id): new_entry},
    )
    save_archive(output_dir, updated)
    return updated


# ---------------------------------------------------------------------------
# Per-generation metadata
# ---------------------------------------------------------------------------


def load_gen_metadata(output_dir: str, gen_id: str | int) -> dict[str, Any]:
    """Load metadata for a specific generation.

    Args:
        output_dir: The path of the output directory.
        gen_id: The ID of the generation.

    Returns:
        The metadata dictionary.

    @since v1.0.0
    @author Muhammad Umer Farooq <umer@lablnet.com>
    """
    meta_path = os.path.join(output_dir, f"gen_{gen_id}", METADATA_FILENAME)
    if not os.path.exists(meta_path):
        return {}
    return json.loads(Path(meta_path).read_text(encoding="utf-8"))


def save_gen_metadata(output_dir: str, gen_id: str | int, metadata: dict[str, Any]) -> None:
    """Save metadata for a specific generation.

    Args:
        output_dir: The path of the output directory.
        gen_id: The ID of the generation.
        metadata: The metadata to save.

    @since v1.0.0
    @author Muhammad Umer Farooq <umer@lablnet.com>
    """
    gen_dir = os.path.join(output_dir, f"gen_{gen_id}")
    os.makedirs(gen_dir, exist_ok=True)
    meta_path = os.path.join(gen_dir, METADATA_FILENAME)
    Path(meta_path).write_text(json.dumps(metadata, indent=2), encoding="utf-8")


def update_gen_metadata(output_dir: str, gen_id: str | int, updates: dict[str, Any]) -> None:
    """Update specific keys in a generation's metadata.

    Args:
        output_dir: The path of the output directory.
        gen_id: The ID of the generation.
        updates: The updates to apply to the metadata.

    @since v1.0.0
    @author Muhammad Umer Farooq <umer@lablnet.com>
    """
    existing = load_gen_metadata(output_dir, gen_id)
    existing.update(updates)
    save_gen_metadata(output_dir, gen_id, existing)


def get_gen_metadata_key(output_dir: str, gen_id: str | int, key: str) -> Any:
    """Get a specific metadata key for a generation.

    Args:
        output_dir: The path of the output directory.
        gen_id: The ID of the generation.
        key: The key to get the metadata for.

    Returns:
        The metadata value.

    @since v1.0.0
    @author Muhammad Umer Farooq <umer@lablnet.com>
    """
    meta = load_gen_metadata(output_dir, gen_id)
    return meta.get(key)


def get_patch_files(output_dir: str, gen_id: str | int) -> list[str]:
    """Get patch files for a generation from its metadata.

    Args:
        output_dir: The path of the output directory.
        gen_id: The ID of the generation.

    Returns:
        The patch files.

    @since v1.0.0
    @author Muhammad Umer Farooq <umer@lablnet.com>
    """
    meta = load_gen_metadata(output_dir, gen_id)
    prev_patches: list[str] = meta.get("prev_patch_files", [])
    curr_patches: list[str] = meta.get("curr_patch_files", [])
    return [*prev_patches, *curr_patches]


# ---------------------------------------------------------------------------
# Score helpers
# ---------------------------------------------------------------------------


def get_score(
    domain: str,
    output_dir: str,
    gen_id: str | int,
    split: str = "train",
) -> float | None:
    """Get the score for a domain/generation combination.

    Args:
        domain: The domain to get the score for.
        output_dir: The path of the output directory.
        gen_id: The ID of the generation.
        split: The split to get the score for.

    Returns:
        The score, or None if not found.

    @since v1.0.0
    @author Muhammad Umer Farooq <umer@lablnet.com>
    """
    eval_dir = f"{domain}_eval" if split == "train" else f"{domain}_eval_{split}"
    report_path = os.path.join(output_dir, f"gen_{gen_id}", eval_dir, "report.json")

    if not os.path.exists(report_path):
        return None

    try:
        report = json.loads(Path(report_path).read_text(encoding="utf-8"))
        return report.get("averageScore")
    except (json.JSONDecodeError, OSError):
        return None


def is_starting_node(gen_id: str | int) -> bool:
    """Check if a generation is a starting node.

    Args:
        gen_id: The ID of the generation.

    Returns:
        True if the generation is a starting node, False otherwise.

    @since v1.0.0
    @author Muhammad Umer Farooq <umer@lablnet.com>
    """
    return gen_id == "initial" or gen_id == 0


def get_avg_score(
    output_dir: str,
    gen_id: str | int,
    domains: list[str],
    split: str = "train",
) -> float | None:
    """Compute the average score for a single generation across all domains.

    Args:
        output_dir: The path of the output directory.
        gen_id: The ID of the generation.
        domains: The names of the domains.
        split: The split to get the score for.

    Returns:
        The average score, or None if not enough data.

    @since v1.0.0
    @author Muhammad Umer Farooq <umer@lablnet.com>
    """
    scores: list[float] = []
    for domain in domains:
        s = get_score(domain, output_dir, gen_id, split)
        if s is not None:
            scores.append(s)

    if len(scores) == len(domains):
        return sum(scores) / len(scores)
    if is_starting_node(gen_id) and len(scores) > 0:
        return sum(scores) / len(scores)
    return None


def get_best_score(
    archive: ArchiveData,
    output_dir: str,
    domains: list[str],
    split: str = "train",
) -> float:
    """Find the best (highest) average score across all generations in the archive.

    Args:
        archive: The archive data.
        output_dir: The path of the output directory.
        domains: The names of the domains.
        split: The split to get the score for.

    Returns:
        The best score.

    @since v1.0.0
    @author Muhammad Umer Farooq <umer@lablnet.com>
    """
    best = -1.0
    for gen_id in archive.archive:
        avg = get_avg_score(output_dir, gen_id, domains, split)
        if avg is not None and avg > best:
            best = avg
    return best
