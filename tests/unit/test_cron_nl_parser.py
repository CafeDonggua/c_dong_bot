from __future__ import annotations

from pathlib import Path
import json

from dongdong_bot.agent.cron_nl_parser import CronNaturalLanguageParser


def _load_cases() -> list[dict[str, str]]:
    root = Path(__file__).resolve().parents[2]
    path = root / "tests" / "data" / "cron_nl_cases.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    return [item for item in payload if isinstance(item, dict)]


def test_cron_nl_parser_matches_fixture_cases() -> None:
    parser = CronNaturalLanguageParser()

    for case in _load_cases():
        name = case["name"]
        parsed = parser.parse(case["text"])
        if case["expected_route"] == "cron_create":
            assert parsed is not None, name
            assert parsed.intent_kind == "repeating", name
            assert parsed.valid, name
            assert parsed.schedule_kind == case["expected_schedule_kind"], name
            assert parsed.schedule_value == case["expected_schedule_value"], name
            assert parsed.title == case["expected_title"], name
            continue

        if case["expected_route"] == "schedule":
            assert parsed is not None, name
            assert parsed.intent_kind == "single_event", name
            continue

        if case["expected_route"] == "clarify":
            assert parsed is not None, name
            assert parsed.intent_kind == "unknown", name
            assert parsed.clarification_hint, name


def test_cron_nl_parser_returns_none_for_unrelated_text() -> None:
    parser = CronNaturalLanguageParser()

    assert parser.parse("你今天過得如何？") is None


def test_cron_nl_parser_requires_time_for_daily_patterns() -> None:
    parser = CronNaturalLanguageParser()

    parsed = parser.parse("每天提醒我喝水")

    assert parsed is not None
    assert parsed.intent_kind == "unknown"
    assert "提醒時間" in parsed.clarification_hint
