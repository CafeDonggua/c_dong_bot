from datetime import datetime

from dongdong_bot.agent.cron_run_store import CronRunStore
from dongdong_bot.agent.cron_store import CronStore
from dongdong_bot.agent.reminder_store import ReminderStore
from dongdong_bot.agent.schedule_store import ScheduleStore
from dongdong_bot.cron.scheduler import CronPayload, ReminderScheduler


def test_once_cron_task_triggers_once_and_marks_completed(tmp_path):
    schedule_store = ScheduleStore(str(tmp_path / "schedules.json"))
    reminder_store = ReminderStore(str(tmp_path / "reminders.json"))
    cron_store = CronStore(str(tmp_path / "cron_tasks.json"))
    cron_run_store = CronRunStore(str(tmp_path / "cron_runs.json"))

    scheduled_at = datetime(2026, 2, 11, 9, 1, 0)
    task = cron_store.create(
        owner_user_id="user-1",
        owner_chat_id="chat-1",
        name="單次提醒",
        message="開會了",
        schedule_kind="at",
        schedule_value=scheduled_at.isoformat(),
        next_run_at=scheduled_at,
    )

    scheduler = ReminderScheduler(
        schedule_store,
        reminder_store,
        cron_store=cron_store,
        cron_run_store=cron_run_store,
    )

    due = scheduler.collect_due(now=datetime(2026, 2, 11, 9, 1, 5))
    assert len(due) == 1
    assert isinstance(due[0], CronPayload)
    assert due[0].task_id == task.task_id

    scheduler.mark_sent(due[0], now=datetime(2026, 2, 11, 9, 1, 6))

    updated = cron_store.get(task.task_id)
    assert updated is not None
    assert updated.status == "completed"
    assert updated.last_status == "ok"
    assert updated.next_run_at is None

    due_again = scheduler.collect_due(now=datetime(2026, 2, 11, 9, 2, 0))
    cron_due_again = [item for item in due_again if isinstance(item, CronPayload)]
    assert cron_due_again == []

    runs = cron_run_store.list(task_id=task.task_id)
    assert len(runs) == 1
    assert runs[0].result == "ok"
