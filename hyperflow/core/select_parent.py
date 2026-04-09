"""Archive parent selection strategies.

@since v1.0.0
@author Muhammad Umer Farooq <umer@lablnet.com>
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Literal

from ..utils.archive import ArchiveData, get_avg_score, get_gen_metadata_key, is_starting_node

SelectionStrategy = Literal["random", "latest", "best", "score_prop", "score_child_prop"]


@dataclass
class _Candidate:
    gen_id: str | int
    score: float


def _get_valid_candidates(
    archive: ArchiveData,
    output_dir: str,
    domains: list[str],
) -> list[_Candidate]:
    """Get the valid candidates from the archive.

    Args:
        archive: The archive data.
        output_dir: The path of the output directory.
        domains: The names of the domains.

    Returns:
        The valid candidates.

    @since v1.0.0
    @author Muhammad Umer Farooq <umer@lablnet.com>
    """
    # Initialize the candidates array.
    candidates: list[_Candidate] = []

    # Iterate through the archive.
    for gen_id in archive.archive:
        # Check if the generation is the starting node.
        if is_starting_node(gen_id):
            valid_parent = True
        else:
            vp = get_gen_metadata_key(output_dir, gen_id, "valid_parent")
            valid_parent = vp is not False
        # If the generation is not a valid parent, continue.
        if not valid_parent:
            continue

        # Get the average score for the generation.
        avg_score = get_avg_score(output_dir, gen_id, domains)
        if avg_score is not None:
            # Add the candidate to the list.
            candidates.append(_Candidate(gen_id=gen_id, score=avg_score))
        elif is_starting_node(gen_id):
            # Add the starting node as a candidate.
            candidates.append(_Candidate(gen_id=gen_id, score=0.0))

    return candidates


def _random_select(candidates: list[_Candidate]) -> str | int:
    """Select a random parent from the candidates.

    Args:
        candidates: The candidates.

    Returns:
        The selected parent generation ID.

    @since v1.0.0
    @author Muhammad Umer Farooq <umer@lablnet.com>
    """
    return random.choice(candidates).gen_id


def _latest_select(candidates: list[_Candidate]) -> str | int:
    """Select the latest parent from the candidates.

    Args:
        candidates: The candidates.

    Returns:
        The selected parent generation ID.

    @since v1.0.0
    @author Muhammad Umer Farooq <umer@lablnet.com>
    """
    return candidates[-1].gen_id


def _best_select(candidates: list[_Candidate]) -> str | int:
    """Select the best parent from the candidates.

    Args:
        candidates: The candidates.

    Returns:
        The selected parent generation ID.
    """
    # Initialize the best candidate.
    best = candidates[0]
    # Iterate through the candidates.
    for c in candidates:
        # Update the best candidate if the current candidate has a higher score.
        if c.score > best.score:
            best = c
    # Return the best candidate.
    return best.gen_id


def _score_prop_select(candidates: list[_Candidate]) -> str | int:
    """Select a parent based on the score (roulette wheel).

    Args:
        candidates: The candidates.

    Returns:
        The selected parent generation ID.

    @since v1.0.0
    @author Muhammad Umer Farooq <umer@lablnet.com>
    """
    # Get the minimum score.
    min_score = min(c.score for c in candidates)
    # Shift the scores to be positive.
    shifted = [(c, c.score - min_score + 0.01) for c in candidates]

    # Get the total weight.
    total_weight = sum(w for _, w in shifted)

    # Generate a random number.
    rand = random.random() * total_weight

    # Select the parent.
    for c, w in shifted:
        rand -= w
        if rand <= 0:
            return c.gen_id

    return shifted[-1][0].gen_id


def _score_child_prop_select(
    candidates: list[_Candidate],
    archive: ArchiveData,
    output_dir: str,
) -> str | int:
    """Select a parent based on the score and child count.

    Args:
        candidates: The candidates.
        archive: The archive data.
        output_dir: The path of the output directory.

    Returns:
        The selected parent generation ID.

    @since v1.0.0
    @author Muhammad Umer Farooq <umer@lablnet.com>
    """
    # Initialize the child counts.
    child_counts: dict[str, int] = {str(c.gen_id): 0 for c in candidates}

    # Iterate through the archive.
    for gen_id in archive.archive:
        # Get the entry.
        entry = archive.entries.get(str(gen_id))
        # If the entry has a parent and the parent is in the candidates, increment the child count.
        if entry and entry.parent_id is not None and str(entry.parent_id) in child_counts:
            child_counts[str(entry.parent_id)] += 1

    # Calculate the weighted scores.
    weighted = [(c, (c.score + 0.01) * (1 / (1 + child_counts.get(str(c.gen_id), 0)))) for c in candidates]

    # Get the total weight.
    total_weight = sum(w for _, w in weighted)
    # Generate a random number.
    rand = random.random() * total_weight

    # Select the parent b
    for c, w in weighted:
        rand -= w
        if rand <= 0:
            return c.gen_id

    return weighted[-1][0].gen_id


def select_parent(
    archive: ArchiveData,
    output_dir: str,
    domains: list[str],
    method: SelectionStrategy = "score_child_prop",
) -> str | int:
    """Select a parent generation from the archive using the given strategy.

    Args:
        archive: The archive data.
        output_dir: The path of the output directory.
        domains: The names of the domains.
        method: The selection strategy.

    Returns:
        The selected parent generation ID.

    @since v1.0.0
    @author Muhammad Umer Farooq <umer@lablnet.com>
    """
    candidates = _get_valid_candidates(archive, output_dir, domains)

    if not candidates:
        raise RuntimeError("No valid parent candidates found in the archive.")

    if method == "random":
        return _random_select(candidates)
    if method == "latest":
        return _latest_select(candidates)
    if method == "best":
        return _best_select(candidates)
    if method == "score_prop":
        return _score_prop_select(candidates)
    if method == "score_child_prop":
        return _score_child_prop_select(candidates, archive, output_dir)

    raise ValueError(f"Unknown selection strategy: {method}")
