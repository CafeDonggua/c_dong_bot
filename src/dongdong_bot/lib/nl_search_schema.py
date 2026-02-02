from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass
class NLSearchPlan:
    is_search: bool
    topic: str
    wants_report: bool = False


@dataclass
class NLSearchResult:
    summary: str
    bullets: List[str]
    sources: List[str]
