from __future__ import annotations

from typing import Any

import great_expectations as gx
import pandas as pd

from core.config import Settings
from core.utils import safe_slug, write_json


def run_data_quality_checks(df: pd.DataFrame, settings: Settings, report_name: str) -> dict[str, Any]:
    """Tao bo data quality checks bang Great Expectations 1.x."""
    context = gx.get_context(mode="ephemeral")
    data_source = context.data_sources.add_pandas(name=f"papers_source_{safe_slug(report_name)}")
    data_asset = data_source.add_dataframe_asset(name="papers_asset")
    batch_def = data_asset.add_batch_definition_whole_dataframe("papers_batch")
    batch = batch_def.get_batch(batch_parameters={"dataframe": df})

    expectations = [
        gx.expectations.ExpectTableRowCountToBeBetween(min_value=5, max_value=5000),
        gx.expectations.ExpectColumnValuesToNotBeNull(column="paper_id"),
        gx.expectations.ExpectColumnValuesToNotBeNull(column="title"),
        gx.expectations.ExpectColumnValuesToNotBeNull(column="text_for_embedding"),
        gx.expectations.ExpectColumnValuesToBeUnique(column="paper_id"),
        gx.expectations.ExpectColumnValueLengthsToBeBetween(column="summary", min_value=30),
    ]

    results = []
    for expectation in expectations:
        result = batch.validate(expectation)
        results.append(
            {
                "expectation_type": expectation.__class__.__name__,
                "success": bool(result.success),
                "result": result.result,
            }
        )

    freshness = build_freshness_report(df, settings, settings.paths.freshness_report)

    overall_success = all(item["success"] for item in results)
    report = {
        "report_name": report_name,
        "success": overall_success,
        "row_count": len(df),
        "expectations": results,
        "freshness": freshness,
    }

    report_path = settings.paths.quality_dir / f"{safe_slug(report_name)}_quality_report.json"
    write_json(report_path, report)
    return report


def build_freshness_report(df: pd.DataFrame, settings: Settings, report_path) -> dict[str, Any]:
    """Tong hop freshness report tu age_days."""
    total_rows = len(df)
    if total_rows == 0:
        payload = {
            "latest_published": None,
            "oldest_published": None,
            "stale_rows": 0,
            "total_rows": 0,
            "stale_ratio": 0.0,
            "is_fresh": False,
        }
        write_json(report_path, payload)
        return payload

    latest_published = df["published"].max()
    oldest_published = df["published"].min()
    stale_rows = int((df["age_days"] > settings.freshness_threshold_days).sum())
    stale_ratio = stale_rows / total_rows

    payload = {
        "latest_published": latest_published,
        "oldest_published": oldest_published,
        "stale_rows": stale_rows,
        "total_rows": total_rows,
        "stale_ratio": stale_ratio,
        "is_fresh": stale_ratio <= 0.25,
    }
    write_json(report_path, payload)
    return payload
