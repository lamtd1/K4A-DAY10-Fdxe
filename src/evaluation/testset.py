from __future__ import annotations

from typing import Any

import pandas as pd

from core.utils import first_sentence, write_json

MIN_DOCUMENTS = 5
QUESTION_TYPES = ("summary", "authors", "date", "categories")


def build_test_set(df: pd.DataFrame, output_path) -> list[dict[str, Any]]:
    """Tao bo evaluation set tu cleaned dataframe."""
    if len(df) < MIN_DOCUMENTS:
        raise ValueError(f"Need at least {MIN_DOCUMENTS} documents to build a test set, got {len(df)}.")

    num_questions = 10
    rows = df.head(num_questions).to_dict(orient="records")
    # Ensure exactly `num_questions` rows by cycling if dataframe is smaller.
    while len(rows) < num_questions:
        rows.append(rows[len(rows) % len(df.to_dict(orient="records"))])
    rows = rows[:num_questions]

    test_set: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        question_type = QUESTION_TYPES[index % len(QUESTION_TYPES)]
        title = row["title"]
        doc_id = row["paper_id"]

        if question_type == "summary":
            question = f"What is the summary of the paper '{title}'?"
            ground_truth = first_sentence(row["summary"])
        elif question_type == "authors":
            question = f"Who authored the paper '{title}'?"
            ground_truth = row["authors_joined"]
        elif question_type == "date":
            question = f"When was the paper '{title}' published?"
            ground_truth = row["published"]
        else:
            question = f"What categories does the paper '{title}' belong to?"
            ground_truth = row["categories_joined"]

        test_set.append(
            {
                "id": f"eval_{index + 1:03d}",
                "question_type": question_type,
                "question": question,
                "ground_truth": ground_truth,
                "ground_truth_doc_ids": [doc_id],
            }
        )

    write_json(output_path, test_set)
    return test_set
