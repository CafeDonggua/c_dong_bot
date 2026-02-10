from datetime import datetime

from dongdong_bot.agent.reminder_store import ReminderStore
from dongdong_bot.agent.schedule_parser import ScheduleCommand, ScheduleParser
from dongdong_bot.agent.schedule_service import ScheduleService
from dongdong_bot.agent.schedule_store import ScheduleStore


def test_completed_query_only_returns_completed_with_status_label(tmp_path):
    schedule_store = ScheduleStore(str(tmp_path / "schedules.json"))
    reminder_store = ReminderStore(str(tmp_path / "reminders.json"))
    service = ScheduleService(schedule_store, reminder_store)

    start_time = datetime(2026, 2, 5, 9, 0)
    scheduled = schedule_store.create(
        user_id="user-1",
        chat_id="chat-1",
        title="上班",
        description="",
        start_time=start_time,
        end_time=None,
        timezone="",
    )
    completed = schedule_store.create(
        user_id="user-1",
        chat_id="chat-1",
        title="剪頭髮",
        description="",
        start_time=start_time,
        end_time=None,
        timezone="",
    )
    schedule_store.complete(completed.schedule_id, completed_at=start_time)

    parser = ScheduleParser()
    command = parser.parse("列出所有已經完成的行程")
    assert command is not None
    assert command.list_range == "completed"

    result = service.handle(command, "user-1", "chat-1")
    assert "剪頭髮" in result.reply
    assert "上班" not in result.reply
    assert "已完成" in result.reply
    assert completed.schedule_id[:8] in result.reply
