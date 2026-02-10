from datetime import datetime

from dongdong_bot.agent.reminder_store import ReminderStore
from dongdong_bot.agent.schedule_parser import ScheduleParser, ScheduleCommand
from dongdong_bot.agent.schedule_service import ScheduleService
from dongdong_bot.agent.schedule_store import ScheduleStore
from dongdong_bot.agent.session import SessionStore


def test_bulk_delete_cancel_keeps_completed_items(tmp_path):
    schedule_store = ScheduleStore(str(tmp_path / "schedules.json"))
    reminder_store = ReminderStore(str(tmp_path / "reminders.json"))
    session_store = SessionStore()
    service = ScheduleService(schedule_store, reminder_store, session_store)
    parser = ScheduleParser()

    schedule = schedule_store.create(
        user_id="user-1",
        chat_id="chat-1",
        title="上班",
        description="",
        start_time=datetime(2026, 2, 6, 9, 0),
        end_time=None,
        timezone="",
    )
    schedule_store.complete(schedule.schedule_id)

    command = parser.parse("刪除全部已完成行程")
    assert command is not None
    result = service.handle(command, "user-1", "chat-1")
    assert "即將刪除" in result.reply

    cancel = parser.parse("取消")
    assert cancel is not None
    assert cancel.action == "bulk_delete_cancel"

    cancelled = service.handle(cancel, "user-1", "chat-1")
    assert "已取消" in cancelled.reply

    list_result = service.handle(
        ScheduleCommand(action="list", title="", list_range="completed"),
        "user-1",
        "chat-1",
    )
    assert "已完成行程" in list_result.reply
