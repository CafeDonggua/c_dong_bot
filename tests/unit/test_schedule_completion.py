from datetime import datetime, timedelta

from dongdong_bot.agent.reminder_store import ReminderStore
from dongdong_bot.agent.schedule_parser import ScheduleCommand
from dongdong_bot.agent.schedule_service import ScheduleService
from dongdong_bot.agent.schedule_store import ScheduleStore
from dongdong_bot.cron.scheduler import ReminderScheduler


def test_reminder_sent_marks_schedule_completed_and_default_list_excludes_completed(tmp_path):
    schedule_store = ScheduleStore(str(tmp_path / "schedules.json"))
    reminder_store = ReminderStore(str(tmp_path / "reminders.json"))

    start_time = datetime(2026, 2, 5, 9, 0)
    schedule = schedule_store.create(
        user_id="user-1",
        chat_id="chat-1",
        title="上班",
        description="",
        start_time=start_time,
        end_time=None,
        timezone="",
    )
    reminder_store.create(schedule.schedule_id, start_time)

    scheduler = ReminderScheduler(schedule_store, reminder_store)
    due = scheduler.collect_due(now=start_time + timedelta(minutes=1))
    assert len(due) == 1

    scheduler.mark_sent(due[0])
    updated = schedule_store.get(schedule.schedule_id)
    assert updated is not None
    assert updated.status == "completed"
    assert updated.completed_at is not None

    service = ScheduleService(schedule_store, reminder_store)
    list_result = service.handle(ScheduleCommand(action="list", title=""), "user-1", "chat-1")
    assert "無未完成行程" in list_result.reply
