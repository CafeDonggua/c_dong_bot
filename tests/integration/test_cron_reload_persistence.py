from datetime import datetime

from dongdong_bot.agent.cron_run_store import CronRunStore
from dongdong_bot.agent.cron_store import CronStore
from dongdong_bot.agent.reminder_store import ReminderStore
from dongdong_bot.agent.schedule_store import ScheduleStore
from dongdong_bot.cron.scheduler import CronPayload, ReminderScheduler


def test_cron_tasks_survive_restart_and_can_still_trigger(tmp_path):
    schedules_path = str(tmp_path / "schedules.json")
    reminders_path = str(tmp_path / "reminders.json")
    cron_tasks_path = str(tmp_path / "cron_tasks.json")
    cron_runs_path = str(tmp_path / "cron_runs.json")

    store_before = CronStore(cron_tasks_path)
    scheduled_at = datetime(2026, 2, 11, 9, 5, 0)
    task = store_before.create(
        owner_user_id="user-1",
        owner_chat_id="chat-1",
        name="重啟後任務",
        message="重啟後仍要觸發",
        schedule_kind="at",
        schedule_value=scheduled_at.isoformat(),
        next_run_at=scheduled_at,
    )

    # Simulate process restart by rebuilding stores/scheduler from persisted files.
    store_after = CronStore(cron_tasks_path)
    scheduler = ReminderScheduler(
        ScheduleStore(schedules_path),
        ReminderStore(reminders_path),
        cron_store=store_after,
        cron_run_store=CronRunStore(cron_runs_path),
    )

    loaded = store_after.list(owner_user_id="user-1")
    assert len(loaded) == 1
    assert loaded[0].task_id == task.task_id
    assert loaded[0].status == "scheduled"

    due = scheduler.collect_due(now=datetime(2026, 2, 11, 9, 5, 1))
    assert len(due) == 1
    assert isinstance(due[0], CronPayload)
    assert due[0].task_id == task.task_id
