from __future__ import annotations

from datetime import datetime

from dongdong_bot.agent.cron_nl_router import CronNLRouter
from dongdong_bot.agent.cron_store import CronStore
from dongdong_bot.agent.reminder_store import ReminderStore
from dongdong_bot.agent.schedule_parser import ScheduleParser
from dongdong_bot.agent.schedule_service import ScheduleService
from dongdong_bot.agent.schedule_store import ScheduleStore


def test_single_event_routes_to_schedule_without_creating_cron(tmp_path) -> None:
    router = CronNLRouter()
    schedule_store = ScheduleStore(str(tmp_path / "schedules.json"))
    reminder_store = ReminderStore(str(tmp_path / "reminders.json"))
    schedule_service = ScheduleService(schedule_store, reminder_store)
    schedule_parser = ScheduleParser()
    cron_store = CronStore(str(tmp_path / "cron_tasks.json"))

    text = "明天下午兩點測試會議"
    decision = router.route(text, now=datetime(2026, 2, 11, 9, 0))
    assert decision.route_target == "schedule"

    command = schedule_parser.parse(text, now=datetime(2026, 2, 11, 9, 0))
    assert command is not None
    assert command.action == "add"
    result = schedule_service.handle(command, user_id="user-1", chat_id="chat-1")
    assert "已新增行程" in result.reply

    assert len(schedule_store.list("user-1")) == 1
    assert cron_store.list(owner_user_id="user-1") == []


def test_schedule_add_list_update_regression_still_works(tmp_path) -> None:
    schedule_store = ScheduleStore(str(tmp_path / "schedules.json"))
    reminder_store = ReminderStore(str(tmp_path / "reminders.json"))
    service = ScheduleService(schedule_store, reminder_store)
    parser = ScheduleParser()

    now = datetime(2026, 2, 11, 9, 0)
    add_command = parser.parse("明天下午兩點測試會議", now=now)
    assert add_command is not None
    add_result = service.handle(add_command, user_id="user-1", chat_id="chat-1")
    assert "已新增行程" in add_result.reply

    list_command = parser.parse("我有哪些行程", now=now)
    assert list_command is not None
    list_result = service.handle(list_command, user_id="user-1", chat_id="chat-1")
    assert "你的行程" in list_result.reply

    schedule = schedule_store.list("user-1")[0]
    update_command = parser.parse(f"修改 {schedule.schedule_id[:8]} 明天 15:30 改成 會議改期", now=now)
    assert update_command is not None
    update_result = service.handle(update_command, user_id="user-1", chat_id="chat-1")
    assert "已更新行程" in update_result.reply
    updated = schedule_store.list("user-1")[0]
    assert updated.title == "會議改期"
    assert updated.start_time == datetime(2026, 2, 12, 15, 30)
