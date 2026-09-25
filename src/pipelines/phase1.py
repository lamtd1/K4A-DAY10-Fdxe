from __future__ import annotations

from core.config import load_settings
from core.utils import now_utc, write_csv, write_json
from evaluation.metrics import evaluate_pipeline
from evaluation.testset import build_test_set
from ingestion.cleaning import build_clean_dataframe
from ingestion.crossref import fetch_source_records
from observability.quality import build_freshness_report, run_data_quality_checks
from observability.reporting import generate_phase1_report
from retrieval.index import LocalEmbeddingIndex


def main() -> None:
    settings = load_settings()

    records = fetch_source_records(settings)
    df = build_clean_dataframe(records, now_utc())

    write_csv(df, settings.paths.clean_csv)
    write_json(settings.paths.clean_json, df.to_dict(orient="records"))

    index = LocalEmbeddingIndex.build(df, settings, embeddings_output_path=settings.paths.embeddings_json)

    if settings.refresh_test_set or not settings.paths.eval_testset.exists():
        build_test_set(df, settings.paths.eval_testset)

    bundle = evaluate_pipeline(
        settings,
        index,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=settings.paths.baseline_metrics,
        answers_output_path=settings.paths.baseline_answers,
    )

    quality = run_data_quality_checks(df, settings, "baseline")
    freshness = build_freshness_report(df, settings, settings.paths.freshness_report)

    source_summary = {
        "source_api": settings.source_api,
        "record_count": len(records),
        "query": settings.source_query,
    }

    generate_phase1_report(
        settings.paths.baseline_report,
        source_summary=source_summary,
        metrics=bundle.summary,
        quality=quality,
        freshness=freshness,
    )

    print(f"Phase 1 complete. Hit rate={bundle.summary['retrieval_hit_rate']:.2f}, token_f1={bundle.summary['mean_token_f1']:.2f}")


if __name__ == "__main__":
    main()
