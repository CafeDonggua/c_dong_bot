from __future__ import annotations

import json
import re
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
            retry_prompt = (
                f"{prompt}\n"
                "請只輸出單行 JSON，不要任何多餘文字或說明。\n"
                f"使用者輸入：{user_text}"
            )
            raw = self.generate(self.model, retry_prompt)
            parsed = self._parse_json(raw)
        url = self._extract_url(user_text)
        if parsed is None and not url:
            return NLSearchPlan(is_search=False, topic="", url="", wants_report=False)
        is_search = bool(parsed.get("is_search", False)) if parsed else False
        topic = str(parsed.get("topic", "") or "").strip() if parsed else ""
        wants_report = bool(parsed.get("wants_report", False)) if parsed else False
        if url:
            is_search = True
        if not wants_report and self._detect_save_intent(user_text):
            wants_report = True
        return NLSearchPlan(
            is_search=is_search,
            topic=topic,
            url=url or "",
            wants_report=wants_report,
        )

    @staticmethod
    def _parse_json(raw: str) -> Optional[dict]:
        raw = raw.strip()
        if not raw:
            return None
        if raw.startswith("```"):
            extracted = NLSearchTopicExtractor._extract_json_from_codeblock(raw)
            if extracted:
                return extracted
        if raw[0] != "{":
            extracted = NLSearchTopicExtractor._extract_json_object(raw)
            if extracted:
                return extracted
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return None

    @staticmethod
    def _extract_json_from_codeblock(raw: str) -> Optional[dict]:
        match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, re.DOTALL)
        if not match:
            return None
        return NLSearchTopicExtractor._extract_json_object(match.group(1))

    @staticmethod
    def _extract_json_object(raw: str) -> Optional[dict]:
        start = raw.find("{")
        end = raw.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return None
        candidate = raw[start : end + 1]
        parsed = NLSearchTopicExtractor._try_json_loads(candidate)
        if parsed is not None:
            return parsed
        cleaned = re.sub(r",\s*([}\]])", r"\1", candidate)
        return NLSearchTopicExtractor._try_json_loads(cleaned)

    @staticmethod
    def _try_json_loads(candidate: str) -> Optional[dict]:
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            return None

    @staticmethod
    def _extract_url(text: str) -> str:
        match = re.search(r"https?://\S+", text)
        if not match:
            return ""
        return match.group(0).rstrip(")")

    @staticmethod
    def _detect_save_intent(text: str) -> bool:
        keywords = ("儲存", "保存", "存檔", "記錄")
        return any(keyword in text for keyword in keywords)
