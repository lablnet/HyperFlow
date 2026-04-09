"""Best-of-archive ensemble: find the best-scoring generation.

@since v1.0.0
@author Muhammad Umer Farooq <umer@lablnet.com>
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from ..utils.archive import get_score, load_archive


def ensemble(
    domain: str,
    question_id: str,
    output_dir: str,
    split: str = "train",
) -> str | None:
    """Best-of-archive ensemble: find the best-scoring generation
    and return its prediction for a specific question.

    Args:
        domain: The domain to ensemble.
        question_id: The ID of the question to ensemble.
        output_dir: The path of the output directory.
        split: The split to ensemble.

    Returns:
        The prediction, or None if not found.

    @since v1.0.0
    @author Muhammad Umer Farooq <umer@lablnet.com>
    """

    # Load the archive data.
    archive_data = load_archive(output_dir)
    # Get the list of generation IDs.
    gen_ids = archive_data.archive

    # Default score
    best_score = -1.0
    best_gen_id: str | int | None = None

    for gen_id in gen_ids:
        # Get the score for the generation.
        score = get_score(domain, output_dir, gen_id, split)
        # Update the best score and generation ID if the score is better.
        if score is not None and score > best_score:
            best_score = score
            best_gen_id = gen_id

    # If no best generation was found, return null.
    if best_gen_id is None:
        return None

    # Get the path to the predictions file.
    eval_dir = f"{domain}_eval" if split == "train" else f"{domain}_eval_{split}"
    predictions_path = os.path.join(output_dir, f"gen_{best_gen_id}", eval_dir, "predictions.json")

    # If the predictions file does not exist, return null.
    if not os.path.exists(predictions_path):
        return None

    try:
        # Load the predictions from the file.
        predictions = json.loads(Path(predictions_path).read_text(encoding="utf-8"))
        # Find the prediction for the given question ID.
        match = next((p for p in predictions if p["questionId"] == question_id), None)
        # Return the prediction if found, otherwise return null.
        return match["prediction"] if match else None
    except Exception:
        return None
