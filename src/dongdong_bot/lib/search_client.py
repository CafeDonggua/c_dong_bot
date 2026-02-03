from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from typing import Any

from openai import NotFoundError, OpenAI, PermissionDeniedError

from dongdong_bot.lib.search_schema import SearchResponse


@dataclass
class SearchClient:
    api_key: str
    model: str

    def __post_init__(self) -> None:
        self._client = OpenAI(api_key=self.api_key)
        self._fallback_models = self._load_fallback_models()

    def search_keyword(self, query: str) -> SearchResponse:
        prompt = (
            "請根據使用者提供的關鍵字搜尋網路資訊，"
            "以 JSON 回覆，欄位包含 summary(摘要), bullets(重點列表), sources(來源連結列表)。"
            "若沒有結果，summary 請回覆空字串，bullets 與 sources 為空陣列。"
        )
        return self._request_json(prompt, query)

    def summarize_link(self, url: str) -> SearchResponse:
        prompt = (
            "請閱讀使用者提供的連結內容並彙整摘要，"
            "以 JSON 回覆，欄位包含 summary(摘要), bullets(重點列表), sources(來源連結列表)。"
            "若無法存取，summary 請回覆空字串，bullets 與 sources 為空陣列。"
        )
        return self._request_json(prompt, url)

    def _request_json(self, system_prompt: str, user_input: str) -> SearchResponse:
        content = ""
        last_error: Exception | None = None
        for model in [self.model, *self._fallback_models]:
            try:
                response = self._client.responses.create(
                    model=model,
                    tools=[{"type": "web_search"}],
                    input=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_input},
                    ],
                )
                content = response.output_text or ""
                last_error = None
                break
            except (NotFoundError, PermissionDeniedError) as exc:
                last_error = exc
                continue
        if last_error is not None:
            raise last_error
        parsed = self._parse_json(content)
        if parsed is None:
            return SearchResponse(summary="", bullets=[], sources=[], raw_text=content)
        return SearchResponse(
            summary=str(parsed.get("summary", "") or ""),
            bullets=[str(item) for item in parsed.get("bullets", []) if item],
            sources=[str(item) for item in parsed.get("sources", []) if item],
            raw_text=content,
        )

    @staticmethod
    def _parse_json(content: str) -> dict[str, Any] | None:
        content = content.strip()
        if not content:
            return None
        if content.startswith("```"):
            extracted = SearchClient._extract_json_from_codeblock(content)
            if extracted:
                return extracted
        if content[0] != "{":
            extracted = SearchClient._extract_json_object(content)
            if extracted:
                return extracted
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return None

    @staticmethod
    def _extract_json_from_codeblock(content: str) -> dict[str, Any] | None:
        match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", content, re.DOTALL)
        if not match:
            return None
        return SearchClient._extract_json_object(match.group(1))

    @staticmethod
    def _extract_json_object(content: str) -> dict[str, Any] | None:
        start = content.find("{")
        end = content.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return None
        candidate = content[start : end + 1]
        parsed = SearchClient._try_json_loads(candidate)
        if parsed is not None:
            return parsed
        cleaned = re.sub(r",\s*([}\]])", r"\1", candidate)
        return SearchClient._try_json_loads(cleaned)

    @staticmethod
    def _try_json_loads(candidate: str) -> dict[str, Any] | None:
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            return None

    @staticmethod
    def _load_fallback_models() -> list[str]:
        raw = os.getenv("SEARCH_FALLBACK_MODELS", "").strip()
        if not raw:
            return []
        return [item.strip() for item in raw.split(",") if item.strip()]
