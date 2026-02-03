from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StyledReply:
    reply: str
    follow_up: str | None = None
    tips: list[str] | None = None


class ResponseStyler:
    _SOFT_PREFIXES = ("好的", "了解", "沒問題", "當然", "可以", "你好", "嗨")
    _TIP_KEYWORDS = (
        "可以做什麼",
        "能做什麼",
        "你會什麼",
        "怎麼用",
        "可以幫我什麼",
        "不知道要",
    )

    def style(self, reply: str, user_text: str) -> StyledReply:
        base = (reply or "").strip()
        base = self._apply_warm_tone(base)
        follow_up = self._pick_follow_up(user_text, base)
        tips = self._pick_tips(user_text)
        merged = self._assemble(base, follow_up, tips)
        merged = self._normalize_lines(merged)
        return StyledReply(reply=merged, follow_up=follow_up, tips=tips)

    def _apply_warm_tone(self, reply: str) -> str:
        if not reply:
            return "了解～"
        if reply.startswith(self._SOFT_PREFIXES):
            return reply
        return f"了解～{reply}"

    def _pick_follow_up(self, user_text: str, reply: str) -> str | None:
        if not user_text or "?" in reply or "？" in reply:
            return None
        if len(reply) > 120:
            return None
        if any(keyword in user_text for keyword in ("怎麼", "如何", "可以")):
            return "你希望我先從哪個部分開始？"
        if any(keyword in user_text for keyword in ("整理", "幫我", "想要")):
            return "你希望我優先處理哪一塊？"
        return "你還想要我幫你補充什麼嗎？"

    def _pick_tips(self, user_text: str) -> list[str]:
        text = user_text.strip()
        if not text:
            return []
        if len(text) <= 4 or any(keyword in text for keyword in self._TIP_KEYWORDS):
            return [
                "你可以說：『記住我喜歡拿鐵』",
                "你可以說：『幫我查台灣能源政策』",
            ]
        return []

    def _assemble(self, base: str, follow_up: str | None, tips: list[str]) -> str:
        blocks = [base]
        if tips:
            tips_block = "\n".join(f"- {tip}" for tip in tips[:2])
            blocks.append(f"你可以試試：\n{tips_block}")
        if follow_up:
            blocks.append(follow_up)
        return "\n\n".join(block for block in blocks if block)

    def _normalize_lines(self, text: str) -> str:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        deduped = []
        for line in lines:
            if not deduped or deduped[-1] != line:
                deduped.append(line)
        if len(deduped) > 8:
            deduped = deduped[:7] + [" ".join(deduped[7:])]
        return "\n".join(deduped)
