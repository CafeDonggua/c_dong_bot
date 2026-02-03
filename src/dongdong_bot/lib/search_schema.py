from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass
class SearchResponse:
    summary: str
    bullets: List[str]
    sources: List[str]
    raw_text: str = ""

    def is_empty(self) -> bool:
        return not (
            _has_text(self.summary)
            or _has_text(self.raw_text)
            or _has_items(self.bullets)
            or _has_items(self.sources)
        )

    def missing_report_sections(self) -> List[str]:
        missing = []
        if not _has_text(self.summary) and not _has_text(self.raw_text):
            missing.append("摘要")
        if not _has_items(self.bullets):
            missing.append("重點")
        if not _has_items(self.sources):
            missing.append("來源")
        return missing


def _has_text(value: str) -> bool:
    return bool(value and value.strip())


def _has_items(values: List[str]) -> bool:
    return any(item and item.strip() for item in values)
