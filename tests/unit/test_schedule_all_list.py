from datetime import datetime

from dongdong_bot.agent.reminder_store import ReminderStore
from dongdong_bot.agent.schedule_parser import ScheduleParser
from dongdong_bot.agent.schedule_service import ScheduleService
from dongdong_bot.agent.schedule_store import ScheduleStore


def test_all_query_returns_scheduled_and_completed_excludes_cancelled(tmp_path):
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
    cancelled = schedule_store.create(
        user_id="user-1",
        chat_id="chat-1",
        title="看醫生",
        description="",
        start_time=start_time,
        end_time=None,
        timezone="",
    )
    schedule_store.complete(completed.schedule_id, completed_at=start_time)
    schedule_store.cancel(cancelled.schedule_id)

    parser = ScheduleParser()
    command = parser.parse("全部行程")
    assert command is not None
    assert command.list_range == "all"

    result = service.handle(command, "user-1", "chat-1")
    assert "上班" in result.reply
    assert "剪頭髮" in result.reply
    assert "看醫生" not in result.reply
    assert "已完成" in result.reply
    assert completed.schedule_id[:8] in result.reply
    assert scheduled.schedule_id[:8] in result.reply
