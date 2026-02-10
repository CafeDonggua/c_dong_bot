from datetime import datetime

from dongdong_bot.agent.reminder_store import ReminderStore
from dongdong_bot.agent.schedule_parser import ScheduleParser
from dongdong_bot.agent.schedule_service import ScheduleService
from dongdong_bot.agent.schedule_store import ScheduleStore


def test_ambiguous_action_prompts_clarification(tmp_path):
    schedule_store = ScheduleStore(str(tmp_path / "schedules.json"))
    reminder_store = ReminderStore(str(tmp_path / "reminders.json"))
    service = ScheduleService(schedule_store, reminder_store)
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

    command = parser.parse(f"把 ID={schedule.schedule_id} 的行程刪除或標示完成")
    assert command is not None
    assert command.action == "clarify"

    result = service.handle(command, "user-1", "chat-1")
    assert "刪除" in result.reply and "完成" in result.reply
