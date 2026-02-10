from datetime import datetime

from dongdong_bot.agent.reminder_store import ReminderStore
from dongdong_bot.agent.schedule_parser import ScheduleParser, ScheduleCommand
from dongdong_bot.agent.schedule_service import ScheduleService
from dongdong_bot.agent.schedule_store import ScheduleStore


def test_delete_by_id_cancels_schedule_and_excludes_from_default_list(tmp_path):
    schedule_store = ScheduleStore(str(tmp_path / "schedules.json"))
    reminder_store = ReminderStore(str(tmp_path / "reminders.json"))
    service = ScheduleService(schedule_store, reminder_store)
    parser = ScheduleParser()

    start_time = datetime(2026, 2, 6, 9, 0)
    schedule = schedule_store.create(
        user_id="user-1",
        chat_id="chat-1",
        title="上班",
        description="",
        start_time=start_time,
        end_time=None,
        timezone="",
    )

    command = parser.parse(f"把ID={schedule.schedule_id[:8]}的上班行程刪除掉")
    assert command is not None
    assert command.action == "delete"
    assert command.schedule_id == schedule.schedule_id[:8]

    result = service.handle(command, "user-1", "chat-1")
    assert "已取消行程" in result.reply

    updated = schedule_store.get(schedule.schedule_id)
    assert updated is not None
    assert updated.status == "cancelled"

    list_result = service.handle(ScheduleCommand(action="list", title=""), "user-1", "chat-1")
    assert "無未完成行程" in list_result.reply
