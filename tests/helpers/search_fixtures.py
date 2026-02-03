from __future__ import annotations

from typing import Iterable, List

from dongdong_bot.lib.search_schema import SearchResponse


def make_search_response(
    summary: str = "",
    bullets: Iterable[str] | None = None,
    sources: Iterable[str] | None = None,
    raw_text: str = "",
) -> SearchResponse:
    return SearchResponse(
        summary=summary,
        bullets=list(bullets or []),
        sources=list(sources or []),
        raw_text=raw_text,
    )


def make_bullets(items: Iterable[str]) -> List[str]:
    return [item for item in items]
