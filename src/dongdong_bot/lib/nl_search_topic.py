from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Callable, Optional

from dongdong_bot.lib.nl_search_schema import NLSearchPlan


@dataclass
class NLSearchTopicExtractor:
    generate: Callable[[str, str], str]
    model: str

    def extract(self, user_text: str) -> NLSearchPlan:
        prompt = (
            "你是搜尋意圖分析器。請判斷使用者是否在要求搜尋或彙整，"
            "並輸出單行 JSON，欄位包含: is_search, topic, wants_report。\n"
            "is_search 為布林值；topic 為精簡可搜尋主題；"
            "wants_report 表示是否要求整理成案例/報告。"
        )
        raw = self.generate(self.model, f"{prompt}\n使用者輸入：{user_text}")
        parsed = self._parse_json(raw)
        if parsed is None:
            return NLSearchPlan(is_search=False, topic="", wants_report=False)
        return NLSearchPlan(
            is_search=bool(parsed.get("is_search", False)),
            topic=str(parsed.get("topic", "") or "").strip(),
            wants_report=bool(parsed.get("wants_report", False)),
        )

    @staticmethod
    def _parse_json(raw: str) -> Optional[dict]:
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return None
