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
        return not (self.summary or self.bullets or self.sources or self.raw_text)
