from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Iterable, List

from dongdong_bot.lib.search_schema import SearchResponse


@dataclass(frozen=True)
class ReportContent:
    summary: str
    bullets: List[str]
    sources: List[str]
    reason: str | None = None
    suggestion: str | None = None


def normalize_report_content(
    response: SearchResponse,
    *,
    reason: str,
    suggestion: str,
) -> ReportContent:
    summary = _clean_text(response.summary)
    bullets = _clean_list(response.bullets)
    sources = _clean_list(response.sources)

    if not summary and response.raw_text:
        summary = _clean_text(response.raw_text)
    if not sources and response.raw_text:
        sources = _extract_urls(response.raw_text)
    if not bullets and summary:
        bullets = [_first_sentence(summary)]

    missing = []
    if not summary:
        missing.append("摘要")
    if not bullets:
        missing.append("重點")
    if not sources:
        missing.append("來源")

    if missing:
        missing_text = "、".join(missing)
        summary = summary or f"無法產出{missing_text}，原因：{reason}"
        if not bullets:
            bullets = [f"原因：{reason}", f"建議：{suggestion}"]
        if not sources:
            sources = [f"無可用來源（{reason}）"]

    return ReportContent(
        summary=summary,
        bullets=bullets,
        sources=sources,
        reason=reason if missing else None,
        suggestion=suggestion if missing else None,
    )


def _clean_text(value: str) -> str:
    return value.strip() if value and value.strip() else ""


def _clean_list(values: Iterable[str]) -> List[str]:
    return [item.strip() for item in values if item and item.strip()]


def _extract_urls(text: str) -> List[str]:
    urls = re.findall(r"https?://\S+", text)
    cleaned = []
    for url in urls:
        cleaned_url = url.rstrip(").,;\"'】>")  # strip common trailing punctuation
        if cleaned_url:
            cleaned.append(cleaned_url)
    seen = set()
    unique = []
    for url in cleaned:
        if url not in seen:
            seen.add(url)
            unique.append(url)
    return unique


def _first_sentence(text: str) -> str:
    for separator in ("。", "！", "？"):
        if separator in text:
            return text.split(separator, 1)[0].strip() + separator
    return text
