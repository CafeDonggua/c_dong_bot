from __future__ import annotations

from datetime import datetime

from dongdong_bot.agent.cron_nl_router import CronNLRouter


def test_cron_nl_router_returns_none_when_not_applicable() -> None:
    router = CronNLRouter()

    decision = router.route("你好，今天天氣如何？", now=datetime(2026, 2, 11, 9, 0))

    assert decision.route_target == "none"
    assert decision.needs_clarification is False


def test_cron_nl_router_prioritizes_repeating_routes() -> None:
    router = CronNLRouter()

    decision = router.route("每 30 分鐘提醒站起來", now=datetime(2026, 2, 11, 9, 0))

    assert decision.route_target == "cron_create"
    assert decision.parse_result is not None
    assert decision.parse_result.schedule_kind == "every"
    assert decision.parse_result.schedule_value == "1800"


def test_cron_nl_router_asks_clarification_for_mixed_signal() -> None:
    router = CronNLRouter()

    decision = router.route("明天開始每天 9 點提醒我開會", now=datetime(2026, 2, 11, 9, 0))

    assert decision.route_target == "clarify"
    assert decision.needs_clarification is True
    assert "單次" in decision.clarification_hint
    assert "重複" in decision.clarification_hint


def test_cron_nl_router_routes_clear_single_event_to_schedule() -> None:
    router = CronNLRouter()

    decision = router.route("明天下午兩點測試會議", now=datetime(2026, 2, 11, 9, 0))

    assert decision.route_target == "schedule"
    assert decision.parse_result is not None
    assert decision.parse_result.intent_kind == "single_event"
