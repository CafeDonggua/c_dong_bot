from datetime import datetime

from dongdong_bot.agent.reminder_store import ReminderStore
from dongdong_bot.agent.schedule_parser import ScheduleParser, ScheduleCommand
from dongdong_bot.agent.schedule_service import ScheduleService
from dongdong_bot.agent.schedule_store import ScheduleStore
from dongdong_bot.agent.session import SessionStore


def _create_completed(schedule_store: ScheduleStore, user_id: str, chat_id: str, title: str) -> str:
    start_time = datetime(2026, 2, 6, 9, 0)
    schedule = schedule_store.create(
        user_id=user_id,
        chat_id=chat_id,
        title=title,
        description="",
        start_time=start_time,
        end_time=None,
        timezone="",
    )
    schedule_store.complete(schedule.schedule_id)
    return schedule.schedule_id


def test_bulk_delete_completed_requires_confirm_and_deletes(tmp_path):
    schedule_store = ScheduleStore(str(tmp_path / "schedules.json"))
    reminder_store = ReminderStore(str(tmp_path / "reminders.json"))
    session_store = SessionStore()
    service = ScheduleService(schedule_store, reminder_store, session_store)
    parser = ScheduleParser()

    _create_completed(schedule_store, "user-1", "chat-1", "上班")
    _create_completed(schedule_store, "user-1", "chat-1", "剪頭髮")

    command = parser.parse("刪除全部已完成行程")
    assert command is not None
    assert command.action == "bulk_delete_completed"

    result = service.handle(command, "user-1", "chat-1")
    assert "即將刪除" in result.reply
    assert "2" in result.reply

    confirm = parser.parse("確認")
    assert confirm is not None
    assert confirm.action == "bulk_delete_confirm"

    confirmed = service.handle(confirm, "user-1", "chat-1")
    assert "已刪除" in confirmed.reply
    assert "2" in confirmed.reply

    list_result = service.handle(
        ScheduleCommand(action="list", title="", list_range="completed"),
        "user-1",
        "chat-1",
    )
    assert "目前沒有已完成行程" in list_result.reply
