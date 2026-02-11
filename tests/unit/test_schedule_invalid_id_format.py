from dongdong_bot.agent.schedule_parser import ScheduleParser
from dongdong_bot.agent.schedule_service import ScheduleService
from dongdong_bot.agent.schedule_store import ScheduleStore
from dongdong_bot.agent.reminder_store import ReminderStore


def test_update_with_non_hex_id_returns_format_error(tmp_path):
    parser = ScheduleParser()
    schedule_store = ScheduleStore(str(tmp_path / "schedules.json"))
    reminder_store = ReminderStore(str(tmp_path / "reminders.json"))
    service = ScheduleService(schedule_store, reminder_store)

    command = parser.parse("修改 252c6v57 改成 會議改期")
    assert command is not None
    assert command.action == "clarify"
    assert command.intent == "invalid"

    result = service.handle(command, user_id="user-1", chat_id="chat-1")
    assert "格式不正確" in result.reply
