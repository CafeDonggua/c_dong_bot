from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from dongdong_bot.agent.cron_nl_parser import CronNLParseResult, CronNaturalLanguageParser


@dataclass(frozen=True)
class CronNLDecision:
    route_target: str
    reason: str
    parse_result: CronNLParseResult | None = None
    needs_clarification: bool = False
    clarification_hint: str = ""


class CronNLRouter:
    def __init__(self, parser: CronNaturalLanguageParser | None = None) -> None:
        self.parser = parser or CronNaturalLanguageParser()

    def route(self, text: str, now: datetime | None = None) -> CronNLDecision:
        parsed = self.parser.parse(text, now=now)
        if parsed is None:
            return CronNLDecision(
                route_target="none",
                reason="not_applicable",
            )

        if parsed.intent_kind == "repeating" and parsed.valid:
            return CronNLDecision(
                route_target="cron_create",
                reason=parsed.reason or "repeating_detected",
                parse_result=parsed,
            )

        if parsed.intent_kind == "single_event":
            return CronNLDecision(
                route_target="schedule",
                reason=parsed.reason or "single_event_detected",
                parse_result=parsed,
            )

        hint = parsed.clarification_hint or (
            "請補充更多資訊，例如：每天 9 點提醒我喝水。"
        )
        return CronNLDecision(
            route_target="clarify",
            reason=parsed.reason or "clarification_required",
            parse_result=parsed,
            needs_clarification=True,
            clarification_hint=hint,
        )
