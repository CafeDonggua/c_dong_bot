from datetime import datetime

from dongdong_bot.agent.reminder_store import ReminderStore
from dongdong_bot.agent.schedule_parser import ScheduleParser, ScheduleCommand
from dongdong_bot.agent.schedule_service import ScheduleService
from dongdong_bot.agent.schedule_store import ScheduleStore


def test_schedule_flow(tmp_path):
    schedule_store = ScheduleStore(str(tmp_path / "schedules.json"))
    reminder_store = ReminderStore(str(tmp_path / "reminders.json"))
    parser = ScheduleParser()
    service = ScheduleService(schedule_store, reminder_store)

    now = datetime(2026, 2, 5, 9, 0)
    command = parser.parse("幫我記錄明天 10:00 開會", now=now)
    assert command is not None
    result = service.handle(command, "user-1", "chat-1")
    assert "已新增行程" in result.reply

    items = schedule_store.list("user-1")
    assert len(items) == 1
    reminders = reminder_store.list_pending()
    assert len(reminders) == 1

    list_command = parser.parse("我有哪些行程", now=now)
    assert list_command is not None
    list_result = service.handle(list_command, "user-1", "chat-1")
    assert "你的行程" in list_result.reply

    update_text = f"修改 {items[0].schedule_id[:8]} 明天 11:00 改成 例會"
    update_command = parser.parse(update_text, now=now)
    assert update_command is not None
    update_result = service.handle(update_command, "user-1", "chat-1")
    assert "已更新行程" in update_result.reply

    updated = schedule_store.list("user-1")[0]
    expected_time = datetime(2026, 2, 6, 11, 0)
    assert updated.title == "例會"
    assert updated.start_time == expected_time

    reminders = reminder_store.list_pending()
    assert len(reminders) == 1
    assert reminders[0].trigger_time == expected_time

    delete_command = ScheduleCommand(action="delete", title="", schedule_id=items[0].schedule_id)
    delete_result = service.handle(delete_command, "user-1", "chat-1")
    assert "已取消行程" in delete_result.reply
