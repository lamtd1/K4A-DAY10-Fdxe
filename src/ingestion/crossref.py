from __future__ import annotations

import re
import time
from dataclasses import dataclass
from pathlib import Path

import requests

from core.config import Settings
from core.utils import normalize_whitespace, read_json, write_json


@dataclass(frozen=True)
class PaperRecord:
    paper_id: str
    title: str
    summary: str
    authors: list[str]
    categories: list[str]
    primary_category: str
    published: str
    updated: str
    abs_url: str
    pdf_url: str
    comment: str


def _strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", " ", text or "")


def _format_date_parts(date_parts: list[int]) -> str:
    if not date_parts:
        return ""
    parts = list(date_parts) + [1, 1]
    year, month, day = parts[0], parts[1], parts[2]
    return f"{year:04d}-{month:02d}-{day:02d}"


def parse_crossref_payload(payload: dict) -> list[PaperRecord]:
    """Parse Crossref payload thanh list PaperRecord."""
    items = payload.get("message", {}).get("items", [])
    records: list[PaperRecord] = []

    for item in items:
        doi = item.get("DOI", "").strip()
        titles = item.get("title") or []
        title = normalize_whitespace(titles[0]) if titles else ""
        if not doi or not title:
            continue

        summary = normalize_whitespace(_strip_html(item.get("abstract", "")))

        authors = [
            normalize_whitespace(f"{author.get('given', '')} {author.get('family', '')}")
            for author in item.get("author", [])
            if author.get("given") or author.get("family")
        ]

        categories = [normalize_whitespace(subject) for subject in item.get("subject", []) if subject]
        primary_category = categories[0] if categories else ""

        published_parts = item.get("published", {}).get("date-parts", [[]])[0]
        published = _format_date_parts(published_parts)

        created_date_time = item.get("created", {}).get("date-time", "")
        updated = created_date_time[:10] if created_date_time else published

        url = item.get("URL", "")

        if not published:
            continue

        records.append(
            PaperRecord(
                paper_id=doi,
                title=title,
                summary=summary,
                authors=authors,
                categories=categories,
                primary_category=primary_category,
                published=published,
                updated=updated,
                abs_url=url,
                pdf_url=url,
                comment=f"Crossref record {doi}",
            )
        )

    return records


def fetch_source_records(settings: Settings) -> list[PaperRecord]:
    """Goi Crossref API, luu raw response, parse thanh records."""
    if not settings.refresh_source and settings.paths.raw_records_json.exists():
        return load_raw_records(settings.paths.raw_records_json)

    params = {
        "query": settings.source_query,
        "filter": settings.source_filter,
        "rows": settings.max_results,
    }

    payload: dict | None = None
    last_error: Exception | None = None
    for attempt in range(3):
        try:
            response = requests.get(
                "https://api.crossref.org/works",
                params=params,
                timeout=30,
                headers={"User-Agent": "day10-data-observability-lab (mailto:student@example.com)"},
            )
            if response.status_code in (429, 503):
                time.sleep(2**attempt)
                continue
            response.raise_for_status()
            payload = response.json()
            break
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            time.sleep(2**attempt)

    if payload is None:
        if settings.paths.raw_api_response.exists():
            payload = read_json(settings.paths.raw_api_response)
        else:
            raise RuntimeError(f"Failed to fetch Crossref data and no offline snapshot available: {last_error}")
    else:
        write_json(settings.paths.raw_api_response, payload)

    records = parse_crossref_payload(payload)
    records = records[: settings.max_results]
    write_json(settings.paths.raw_records_json, [record.__dict__ for record in records])
    return records


def load_raw_records(path: Path) -> list[PaperRecord]:
    """Doc JSON snapshot va map thanh PaperRecord."""
    raw = read_json(path)
    return [PaperRecord(**item) for item in raw]
