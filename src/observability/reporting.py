from __future__ import annotations

from typing import Any

from core.utils import write_text


def generate_phase1_report(
    report_path,
    source_summary: dict[str, Any],
    metrics: dict[str, Any],
    quality: dict[str, Any],
    freshness: dict[str, Any],
) -> None:
    """Viet markdown report cho baseline phase."""
    lines = [
        "# Phase 1 Baseline Report",
        "",
        "## Source Summary",
        "",
        f"- Source API: {source_summary.get('source_api', 'N/A')}",
        f"- Records fetched: {source_summary.get('record_count', 'N/A')}",
        f"- Query: {source_summary.get('query', 'N/A')}",
        "",
        "## Retrieval / Evaluation Metrics",
        "",
        f"- Samples: {metrics.get('samples', 'N/A')}",
        f"- Retrieval hit rate: {metrics.get('retrieval_hit_rate', 'N/A')}",
        f"- Mean token F1: {metrics.get('mean_token_f1', 'N/A')}",
        f"- Judge accuracy: {metrics.get('judge_accuracy', 'N/A')}",
        f"- Mean judge score: {metrics.get('mean_judge_score', 'N/A')}",
        "",
        "## Data Quality",
        "",
        f"- Success: {quality.get('success', 'N/A')}",
        f"- Row count: {quality.get('row_count', 'N/A')}",
        "",
        "## Freshness",
        "",
        f"- Total rows: {freshness.get('total_rows', 'N/A')}",
        f"- Stale rows: {freshness.get('stale_rows', 'N/A')}",
        f"- Stale ratio: {freshness.get('stale_ratio', 'N/A')}",
        f"- Is fresh: {freshness.get('is_fresh', 'N/A')}",
        f"- Latest published: {freshness.get('latest_published', 'N/A')}",
        f"- Oldest published: {freshness.get('oldest_published', 'N/A')}",
        "",
    ]
    write_text(report_path, "\n".join(lines))


def generate_corruption_report(
    report_path,
    baseline_metrics: dict[str, Any],
    corrupted_metrics: dict[str, Any],
    repaired_metrics: dict[str, Any],
    corrupted_quality: dict[str, Any],
    repaired_quality: dict[str, Any],
    corrupted_freshness: dict[str, Any],
    repaired_freshness: dict[str, Any],
) -> None:
    """Viet markdown report so sanh baseline/corrupted/repaired."""

    def metric_row(label: str, key: str) -> str:
        return (
            f"| {label} | {baseline_metrics.get(key, 'N/A')} "
            f"| {corrupted_metrics.get(key, 'N/A')} | {repaired_metrics.get(key, 'N/A')} |"
        )

    lines = [
        "# Data Corruption & Repair Comparison Report",
        "",
        "## Metrics Comparison",
        "",
        "| Metric | Baseline | Corrupted | Repaired |",
        "| --- | --- | --- | --- |",
        metric_row("Retrieval hit rate", "retrieval_hit_rate"),
        metric_row("Mean token F1", "mean_token_f1"),
        metric_row("Judge accuracy", "judge_accuracy"),
        metric_row("Mean judge score", "mean_judge_score"),
        "",
        "## Data Quality",
        "",
        f"- Corrupted quality success: {corrupted_quality.get('success', 'N/A')}",
        f"- Repaired quality success: {repaired_quality.get('success', 'N/A')}",
        "",
        "## Freshness",
        "",
        f"- Corrupted is_fresh: {corrupted_freshness.get('is_fresh', 'N/A')}",
        f"- Repaired is_fresh: {repaired_freshness.get('is_fresh', 'N/A')}",
        "",
    ]
    write_text(report_path, "\n".join(lines))
