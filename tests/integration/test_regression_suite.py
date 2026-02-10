from __future__ import annotations

from datetime import datetime
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dongdong_bot.agent.reminder_store import ReminderStore
from dongdong_bot.agent.schedule_parser import ScheduleParser
from dongdong_bot.agent.schedule_service import ScheduleService
from dongdong_bot.agent.schedule_store import ScheduleStore
from dongdong_bot.lib.search_formatter import SearchFormatter
from dongdong_bot.lib.search_schema import SearchResponse
from dongdong_bot.main import _handle_search_command, _has_memory_keywords, _is_explicit_memory_save
from tests.helpers.regression_loader import load_regression_cases


class _StubSearchClient:
    def search_keyword(self, query: str) -> SearchResponse:
        return SearchResponse(
            summary=f"摘要：{query}",
            bullets=["重點 1", "重點 2"],
            sources=["https://example.com"],
        )


def _cases_by(category: str):
    cases = load_regression_cases(ROOT)
    return [case for case in cases if case.category == category]


def test_regression_cases_present():
    cases = load_regression_cases(ROOT)
    assert cases, "回歸測試案例不可為空"


def test_memory_save_cases():
    for case in _cases_by("memory_save"):
        assert _is_explicit_memory_save(case.input_text)


def test_memory_query_cases():
    for case in _cases_by("memory_query"):
        assert _has_memory_keywords(case.input_text)


def test_schedule_add_cases():
    parser = ScheduleParser()
    now = datetime(2026, 2, 5, 9, 0)
    for case in _cases_by("schedule_add"):
        command = parser.parse(case.input_text, now=now)
        assert command is not None
        assert command.action == "add"
        assert command.start_time is not None


def test_schedule_list_cases():
    parser = ScheduleParser()
    for case in _cases_by("schedule_list"):
        command = parser.parse(case.input_text)
        assert command is not None
        assert command.action == "list"


def test_search_report_cases():
    formatter = SearchFormatter()
    client = _StubSearchClient()
    for case in _cases_by("search_report"):
        reply = _handle_search_command(case.input_text, client, formatter)
        assert "摘要" in reply


def test_schedule_flow_regression():
    schedule_store = ScheduleStore(str(ROOT / "tests" / "data" / "tmp_schedules.json"))
    reminder_store = ReminderStore(str(ROOT / "tests" / "data" / "tmp_reminders.json"))
    service = ScheduleService(schedule_store, reminder_store)

    parser = ScheduleParser()
    now = datetime(2026, 2, 5, 9, 0)
    command = parser.parse("幫我記錄明天 10:00 開會", now=now)
    assert command is not None
    result = service.handle(command, "user-1", "chat-1")
    assert "已新增行程" in result.reply

    list_command = parser.parse("我有哪些行程", now=now)
    assert list_command is not None
    list_result = service.handle(list_command, "user-1", "chat-1")
    assert "你的行程" in list_result.reply

    # cleanup
    (ROOT / "tests" / "data" / "tmp_schedules.json").unlink(missing_ok=True)
    (ROOT / "tests" / "data" / "tmp_reminders.json").unlink(missing_ok=True)
