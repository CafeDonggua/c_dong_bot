from __future__ import annotations

from dataclasses import dataclass
import json
import time
from typing import Any, Callable, Dict, List, Optional, Tuple


IntentClassifierFn = Callable[[str], tuple[str | None, float]]
INTENT_SCORE_THRESHOLD = 0.78


@dataclass
class StepResult:
    goal: str
    action: str
    observation: str
    reply: str
    progress: bool
    memory_save: bool = False
    memory_content: Optional[str] = None
    memory_query: Optional[str] = None
    memory_date: Optional[str] = None
    memory_date_range: Optional[Dict[str, str]] = None


@dataclass
class BotResponse:
    reply: str
    stop_reason: Optional[str]
    decision: str
    tool_reason: Optional[str] = None
    memory_content: Optional[str] = None
    memory_query: Optional[str] = None
    memory_date: Optional[str] = None
    memory_date_range: Optional[Dict[str, str]] = None


class GoapEngine:
    def __init__(
        self,
        llm_client,
        model: str,
        fast_model: str,
        intent_classifier: IntentClassifierFn | None = None,
        shortcuts_enabled: bool = True,
        base_max_iters: int = 3,
        max_iters_cap: int = 6,
        no_progress_limit: int = 3,
        json_retry_limit: int = 1,
        perf_log: bool = False,
    ) -> None:
        self.llm_client = llm_client
        self.model = model
        self.fast_model = fast_model
        self.intent_classifier = intent_classifier
        self.shortcuts_enabled = shortcuts_enabled
        self.base_max_iters = base_max_iters
        self.max_iters_cap = max_iters_cap
        self.no_progress_limit = no_progress_limit
        self.json_retry_limit = json_retry_limit
        self.perf_log = perf_log

    def respond(self, user_text: str) -> BotResponse:
        start_time = time.perf_counter()
        if self.shortcuts_enabled:
            decision, reason = self._route_intent(user_text)
            if self._should_direct_reply(user_text, decision):
                reply = self._direct_reply(user_text)
                if self.perf_log:
                    elapsed_ms = (time.perf_counter() - start_time) * 1000
                    print(f"[perf] goap.direct_reply total_ms={elapsed_ms:.1f}")
                return BotResponse(
                    reply=reply,
                    stop_reason=None,
                    decision="direct_reply",
                    tool_reason=reason,
                )
            if decision == "memory_save":
                content = self._extract_memory_content(user_text)
                if content:
                    return BotResponse(
                        reply="已記住。",
                        stop_reason=None,
                        decision=decision,
                        memory_content=content,
                    )
            if decision == "memory_query":
                return BotResponse(
                    reply="我幫你查一下。",
                    stop_reason=None,
                    decision=decision,
                    memory_query=user_text.strip(),
                )
            if decision == "use_tool":
                reply = (
                    "這個問題需要即時工具或外部資料，但目前工具尚未啟用。"
                    "若你希望我改用一般知識回答，請告訴我。"
                )
                if self.perf_log:
                    elapsed_ms = (time.perf_counter() - start_time) * 1000
                    print(f"[perf] goap.tool_stub total_ms={elapsed_ms:.1f}")
                return BotResponse(
                    reply=reply,
                    stop_reason=None,
                    decision=decision,
                    tool_reason=reason,
                )
        else:
            decision, reason = "goap", None

        history: List[StepResult] = []
        max_iters = self.base_max_iters
        stop_reason = None
        no_progress_streak = 0

        iters = 0
        while iters < max_iters:
            step = self._next_step(user_text, history)
            history.append(step)
            iters += 1

            if not step.progress and self._is_repeating(history):
                stop_reason = "loop_detected"
                break
            if not step.progress:
                no_progress_streak += 1
                if no_progress_streak >= self.no_progress_limit:
                    stop_reason = "no_progress"
                    break
            else:
                no_progress_streak = 0

            if step.progress and max_iters < self.max_iters_cap:
                max_iters += 1

        final_reply = history[-1].reply if history else "目前無法處理，請稍後再試。"
        if stop_reason:
            final_reply += "\n\n我偵測到重複迴圈，已停止以避免無進展消耗。"
        memory_content = None
        memory_query = None
        memory_date = None
        memory_date_range = None
        for step in reversed(history):
            if step.memory_save and step.memory_content:
                memory_content = step.memory_content.strip()
                break
        for step in reversed(history):
            if step.memory_query:
                memory_query = step.memory_query.strip()
                memory_date = step.memory_date
                memory_date_range = step.memory_date_range
                break
        response = BotResponse(
            reply=final_reply,
            stop_reason=stop_reason,
            decision=decision,
            tool_reason=reason,
            memory_content=memory_content,
            memory_query=memory_query,
            memory_date=memory_date,
            memory_date_range=memory_date_range,
        )
        if self.perf_log:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            print(f"[perf] goap.respond total_ms={elapsed_ms:.1f}")
        return response

    def _should_direct_reply(self, user_text: str, decision: str) -> bool:
        return decision == "direct_reply"

    def _route_intent(self, user_text: str) -> Tuple[str, Optional[str]]:
        if self.intent_classifier is not None:
            intent, score = self.intent_classifier(user_text)
            if intent and score >= INTENT_SCORE_THRESHOLD:
                if intent in {"memory_query", "memory_save", "use_tool"}:
                    return intent, f"語意判斷:{intent}"
        return "direct_reply", None

    def _is_repeating(self, history: List[StepResult]) -> bool:
        if len(history) < 2:
            return False
        last_obs = history[-1].observation.strip()
        prev_obs = history[-2].observation.strip()
        if last_obs and last_obs == prev_obs:
            return True
        last_reply = history[-1].reply.strip()
        prev_reply = history[-2].reply.strip()
        return last_reply and last_reply == prev_reply

    def _next_step(self, user_text: str, history: List[StepResult]) -> StepResult:
        prompt = self._build_prompt(user_text, history)
        parsed = self._request_json(prompt)

        return StepResult(
            goal=parsed.get("goal", "理解使用者需求"),
            action=parsed.get("action", "產生回覆"),
            observation=parsed.get("observation", "無"),
            reply=parsed.get("reply", "我已理解你的需求。"),
            progress=bool(parsed.get("progress", False)),
            memory_save=bool(parsed.get("memory_save", False)),
            memory_content=parsed.get("memory_content") or None,
            memory_query=parsed.get("memory_query") or None,
            memory_date=parsed.get("memory_date") or None,
            memory_date_range=parsed.get("memory_date_range") or None,
        )

    def _direct_reply(self, user_text: str) -> str:
        prompt = (
            "你是 Telegram 個人助理，請直接回覆使用者的問題。\n"
            "回覆需簡潔、清楚，且避免要求多輪確認。\n\n"
            f"使用者輸入: {user_text}\n"
        )
        return (
            self.llm_client.generate(model=self.fast_model, prompt=prompt).strip()
            or "我已理解你的需求。"
        )

    @staticmethod
    def _extract_memory_content(user_text: str) -> Optional[str]:
        for keyword in ("記住", "記下", "備忘"):
            if keyword in user_text:
                content = user_text.split(keyword, 1)[1].strip()
                content = content.strip(" ：:，,。.!？?　")
                if content:
                    return content
        return None

    def _build_prompt(self, user_text: str, history: List[StepResult]) -> str:
        history_lines = []
        for idx, step in enumerate(history, start=1):
            history_lines.append(
                f"步驟 {idx}: 目標={step.goal} 行動={step.action} 觀察={step.observation}"
            )
        history_block = "\n".join(history_lines) if history_lines else "(無)"

        return (
            "你是目標導向的 Telegram 機器人。\n"
            "請以單行 JSON 回覆，禁止額外文字或註解。\n"
            "欄位包含: goal, action, observation, reply, progress, memory_save, memory_content, memory_query, memory_date, memory_date_range。\n"
            "progress 為是否有進展的布林值。\n\n"
            f"使用者輸入: {user_text}\n"
            f"歷史步驟: {history_block}\n"
            "若使用者要求記住事情，memory_save 設為 true，memory_content 填入要記住的內容。\n"
            "若使用者要求回憶，memory_query 填入查詢關鍵詞；可選 memory_date 或 memory_date_range。\n"
        )

    def _request_json(self, prompt: str) -> Dict[str, Any]:
        last_raw = ""
        for attempt in range(self.json_retry_limit + 1):
            call_start = time.perf_counter()
            raw = self.llm_client.generate(model=self.model, prompt=prompt)
            if self.perf_log:
                call_ms = (time.perf_counter() - call_start) * 1000
                print(f"[perf] openai.generate attempt={attempt + 1} ms={call_ms:.1f}")
            last_raw = raw
            parsed = self._parse_json(raw)
            if parsed is not None:
                return parsed
            if attempt < self.json_retry_limit:
                prompt = (
                    "請僅輸出單行 JSON，不要包含任何額外文字。\n\n"
                    + prompt
                )
        return self._fallback_json(last_raw)

    def _parse_json(self, raw: str) -> Optional[Dict[str, Any]]:
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return None

    def _fallback_json(self, raw: str) -> Dict[str, Any]:
        return {
            "goal": "理解使用者需求",
            "action": "產生回覆",
            "observation": "無法解析 JSON，改用直接回覆",
            "reply": raw.strip() or "我已理解你的需求。",
            "progress": True,
            "memory_save": False,
            "memory_content": None,
            "memory_query": None,
            "memory_date": None,
            "memory_date_range": None,
        }
