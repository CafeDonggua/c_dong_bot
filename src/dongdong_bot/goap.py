from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any, Dict, List, Optional, Tuple


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
    memory_content: Optional[str] = None
    memory_query: Optional[str] = None
    memory_date: Optional[str] = None
    memory_date_range: Optional[Dict[str, str]] = None


class GoapEngine:
    def __init__(
        self,
        llm_client,
        model: str,
        base_max_iters: int = 3,
        max_iters_cap: int = 6,
        no_progress_limit: int = 3,
        json_retry_limit: int = 1,
    ) -> None:
        self.llm_client = llm_client
        self.model = model
        self.base_max_iters = base_max_iters
        self.max_iters_cap = max_iters_cap
        self.no_progress_limit = no_progress_limit
        self.json_retry_limit = json_retry_limit

    def respond(self, user_text: str) -> BotResponse:
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
        return BotResponse(
            reply=final_reply,
            stop_reason=stop_reason,
            memory_content=memory_content,
            memory_query=memory_query,
            memory_date=memory_date,
            memory_date_range=memory_date_range,
        )

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
            raw = self.llm_client.generate(model=self.model, prompt=prompt)
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
