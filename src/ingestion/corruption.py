from __future__ import annotations

from datetime import datetime, timedelta

import pandas as pd

from core.utils import write_json


def _rebuild_text_for_embedding(row: pd.Series) -> str:
    return (
        f"Title: {row['title']}\n"
        f"Authors: {row['authors_joined']}\n"
        f"Published: {row['published']}\n"
        f"Categories: {row['categories_joined']}\n"
        f"Summary: {row['summary']}"
    )


def corrupt_clean_dataframe(df: pd.DataFrame, output_log_path) -> pd.DataFrame:
    """Simulate nhieu dang data corruption tren clean dataframe."""
    df = df.sort_values(by="published", ascending=False).reset_index(drop=True)
    log: dict[str, object] = {}

    # 1. Drop 20% cac ban ghi moi nhat.
    drop_count = max(1, int(len(df) * 0.2))
    dropped_ids = df.iloc[:drop_count]["paper_id"].tolist()
    df = df.iloc[drop_count:].reset_index(drop=True)
    log["dropped_latest_records"] = dropped_ids

    # 2. Blank summary o mot so dong.
    blank_count = max(1, int(len(df) * 0.15))
    blank_indices = df.index[:blank_count]
    blanked_ids = df.loc[blank_indices, "paper_id"].tolist()
    df.loc[blank_indices, "summary"] = ""
    log["blanked_summary_records"] = blanked_ids

    # 3. Chen noise vao tom tat.
    noise_count = max(1, int(len(df) * 0.15))
    noise_indices = df.index[blank_count : blank_count + noise_count]
    noised_ids = df.loc[noise_indices, "paper_id"].tolist()
    df.loc[noise_indices, "summary"] = df.loc[noise_indices, "summary"] + " ###@@@garbled-noise@@@###"
    log["noise_injected_records"] = noised_ids

    # 4. Cat ngan title.
    truncate_count = max(1, int(len(df) * 0.15))
    truncate_start = blank_count + noise_count
    truncate_indices = df.index[truncate_start : truncate_start + truncate_count]
    truncated_ids = df.loc[truncate_indices, "paper_id"].tolist()
    df.loc[truncate_indices, "title"] = df.loc[truncate_indices, "title"].str.slice(0, 8)
    log["truncated_title_records"] = truncated_ids

    # 5. Lam published date cu di (365 ngay).
    stale_count = max(1, int(len(df) * 0.15))
    stale_start = truncate_start + truncate_count
    stale_indices = df.index[stale_start : stale_start + stale_count]
    staled_ids = df.loc[stale_indices, "paper_id"].tolist()

    def _stale_date(value: str) -> str:
        try:
            date = datetime.fromisoformat(value)
        except ValueError:
            return value
        return (date - timedelta(days=365)).date().isoformat()

    df.loc[stale_indices, "published"] = df.loc[stale_indices, "published"].apply(_stale_date)
    df.loc[stale_indices, "age_days"] = df.loc[stale_indices, "age_days"] + 365
    log["stale_date_records"] = staled_ids

    # 6. Nhan doi so dong bang dung so dong da drop, giu nguyen tong so dong ban dau.
    duplicate_count = drop_count
    duplicate_rows = df.iloc[:duplicate_count]
    duplicated_ids = duplicate_rows["paper_id"].tolist()
    df = pd.concat([df, duplicate_rows], ignore_index=True)
    log["duplicated_records"] = duplicated_ids

    # 7. Rebuild text_for_embedding sau khi corrupt.
    df["summary_chars"] = df["summary"].str.len()
    df["text_for_embedding"] = df.apply(_rebuild_text_for_embedding, axis=1)

    log["total_rows_after_corruption"] = len(df)
    write_json(output_log_path, log)

    return df
