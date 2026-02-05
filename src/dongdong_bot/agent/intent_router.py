from __future__ import annotations

from dataclasses import dataclass
import json
import re
from typing import Callable, Optional

from dongdong_bot.agent.capability_catalog import CapabilityCatalog


@dataclass(frozen=True)
class IntentDecision:
    capability: str
    missing_inputs: list[str]
    needs_clarification: bool
    confidence: float
    reason: str | None = None


class IntentRouter:
    def __init__(
        self,
        generate: Callable[[str, str], str],
        model: str,
        catalog: CapabilityCatalog,
    ) -> None:
        self._generate = generate
        self._model = model
        self._catalog = catalog

    def route(self, user_text: str) -> IntentDecision:
        if not user_text.strip():
            return IntentDecision(
                capability="direct_reply",
                missing_inputs=["intent"],
                needs_clarification=True,
                confidence=0.0,
                reason="empty_input",
            )
        prompt = self._build_prompt(user_text)
        raw = self._generate(self._model, prompt)
        parsed = self._parse_json(raw)
        if parsed is None:
            return IntentDecision(
                capability="direct_reply",
                missing_inputs=["intent"],
                needs_clarification=True,
                confidence=0.0,
                reason="parse_failed",
            )
        decision = self._build_decision(parsed)
        if decision.capability not in self._catalog.capability_names():
            return IntentDecision(
                capability="direct_reply",
                missing_inputs=["intent"],
                needs_clarification=True,
                confidence=0.0,
                reason="invalid_capability",
            )
        return decision

    def build_clarification_question(self, decision: IntentDecision) -> str:
        capability = self._catalog.get(decision.capability)
        if not capability:
            return "可以再說清楚你想要我做什麼嗎？"
        for field in decision.missing_inputs:
            question = capability.clarifications.get(field)
            if question:
                return question
        if decision.needs_clarification:
            return "可以再補充一些細節嗎？"
        return "可以再說清楚你想要我做什麼嗎？"

    def _build_prompt(self, user_text: str) -> str:
        catalog_block = self._catalog.to_prompt_block()
        capability_names = ", ".join(self._catalog.capability_names())
        return (
            "你是意圖路由器，請根據使用者輸入選擇最適合的功能。\n"
            "請只輸出單行 JSON，不要任何額外文字。\n"
            "欄位包含: capability, missing_inputs, needs_clarification, confidence, reason。\n"
            "capability 必須是以下之一: "
            f"{capability_names}\n"
            "missing_inputs 為缺少的必要資訊列表，若無缺少請填空陣列。\n"
            "missing_inputs 僅能從該能力的 required_inputs 中選擇。\n"
            "needs_clarification 為布林值，當意圖不明確或有缺少資訊時設為 true。\n"
            "confidence 為 0~1 之間的小數。\n\n"
            "可用功能清單:\n"
            f"{catalog_block}\n\n"
            f"使用者輸入: {user_text}\n"
        )

    def _build_decision(self, parsed: dict) -> IntentDecision:
        capability = str(parsed.get("capability", "")).strip() or "direct_reply"
        missing_inputs = parsed.get("missing_inputs", [])
        if not isinstance(missing_inputs, list):
            missing_inputs = []
        missing_inputs = [str(item) for item in missing_inputs if str(item).strip()]
        needs_clarification = bool(parsed.get("needs_clarification", False))
        if missing_inputs and not needs_clarification:
            needs_clarification = True
        confidence_raw = parsed.get("confidence", 0.0)
        try:
            confidence = float(confidence_raw)
        except (TypeError, ValueError):
            confidence = 0.0
        reason = parsed.get("reason")
        if reason is not None:
            reason = str(reason)
        return IntentDecision(
            capability=capability,
            missing_inputs=missing_inputs,
            needs_clarification=needs_clarification,
            confidence=confidence,
            reason=reason,
        )

    @staticmethod
    def _parse_json(raw: str) -> Optional[dict]:
        raw = raw.strip()
        if not raw:
            return None
        if raw.startswith("```"):
            extracted = IntentRouter._extract_json_from_codeblock(raw)
            if extracted:
                return extracted
        if raw[0] != "{":
            extracted = IntentRouter._extract_json_object(raw)
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
        return IntentRouter._extract_json_object(match.group(1))

    @staticmethod
    def _extract_json_object(raw: str) -> Optional[dict]:
        start = raw.find("{")
        end = raw.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return None
        candidate = raw[start : end + 1]
        parsed = IntentRouter._try_json_loads(candidate)
        if parsed is not None:
            return parsed
        cleaned = re.sub(r",\s*([}\]])", r"\1", candidate)
        return IntentRouter._try_json_loads(cleaned)

    @staticmethod
    def _try_json_loads(candidate: str) -> Optional[dict]:
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            return None
