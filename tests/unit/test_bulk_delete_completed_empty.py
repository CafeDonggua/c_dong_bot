from datetime import datetime

from dongdong_bot.agent.reminder_store import ReminderStore
from dongdong_bot.agent.schedule_parser import ScheduleParser
from dongdong_bot.agent.schedule_service import ScheduleService
from dongdong_bot.agent.schedule_store import ScheduleStore
from dongdong_bot.agent.session import SessionStore


def test_bulk_delete_completed_empty_returns_message(tmp_path):
    schedule_store = ScheduleStore(str(tmp_path / "schedules.json"))
    reminder_store = ReminderStore(str(tmp_path / "reminders.json"))
    session_store = SessionStore()
    service = ScheduleService(schedule_store, reminder_store, session_store)
    parser = ScheduleParser()

    schedule_store.create(
        user_id="user-1",
        chat_id="chat-1",
        title="上班",
        description="",
        start_time=datetime(2026, 2, 6, 9, 0),
        end_time=None,
        timezone="",
    )

    command = parser.parse("刪除全部已完成行程")
    assert command is not None
    assert command.action == "bulk_delete_completed"

    result = service.handle(command, "user-1", "chat-1")
    assert "沒有已完成行程可刪除" in result.reply
    assert not service.has_pending_bulk_delete("user-1")
