from datetime import datetime

from dongdong_bot.agent.cron_run_store import CronRunStore
from dongdong_bot.agent.cron_store import CronStore
from dongdong_bot.agent.reminder_store import ReminderStore
from dongdong_bot.agent.schedule_store import ScheduleStore
from dongdong_bot.cron.scheduler import CronPayload, ReminderScheduler


def test_repeating_cron_updates_next_run_and_triggers_multiple_times(tmp_path):
    schedule_store = ScheduleStore(str(tmp_path / "schedules.json"))
    reminder_store = ReminderStore(str(tmp_path / "reminders.json"))
    cron_store = CronStore(str(tmp_path / "cron_tasks.json"))
    cron_run_store = CronRunStore(str(tmp_path / "cron_runs.json"))

    task = cron_store.create(
        owner_user_id="user-1",
        owner_chat_id="chat-1",
        name="每分鐘提醒",
        message="喝水",
        schedule_kind="every",
        schedule_value="60",
        next_run_at=datetime(2026, 2, 11, 9, 1, 0),
    )
    scheduler = ReminderScheduler(
        schedule_store,
        reminder_store,
        cron_store=cron_store,
        cron_run_store=cron_run_store,
    )

    first_due = scheduler.collect_due(now=datetime(2026, 2, 11, 9, 1, 0))
    assert len(first_due) == 1
    assert isinstance(first_due[0], CronPayload)
    scheduler.mark_sent(first_due[0], now=datetime(2026, 2, 11, 9, 1, 0))

    after_first = cron_store.get(task.task_id)
    assert after_first is not None
    assert after_first.status == "scheduled"
    assert after_first.next_run_at == datetime(2026, 2, 11, 9, 2, 0)

    second_due = scheduler.collect_due(now=datetime(2026, 2, 11, 9, 2, 0))
    assert len(second_due) == 1
    assert isinstance(second_due[0], CronPayload)
    scheduler.mark_sent(second_due[0], now=datetime(2026, 2, 11, 9, 2, 0))

    runs = cron_run_store.list(task_id=task.task_id)
    assert len(runs) == 2
    assert runs[0].result == "ok"
    assert runs[1].result == "ok"

    after_second = cron_store.get(task.task_id)
    assert after_second is not None
    assert after_second.next_run_at == datetime(2026, 2, 11, 9, 3, 0)


def test_collect_due_deduplicates_same_task_in_same_round(tmp_path):
    schedule_store = ScheduleStore(str(tmp_path / "schedules.json"))
    reminder_store = ReminderStore(str(tmp_path / "reminders.json"))
    cron_store = CronStore(str(tmp_path / "cron_tasks.json"))
    cron_run_store = CronRunStore(str(tmp_path / "cron_runs.json"))

    cron_store.create(
        owner_user_id="user-1",
        owner_chat_id="chat-1",
        name="同輪去重",
        message="只送一次",
        schedule_kind="every",
        schedule_value="60",
        next_run_at=datetime(2026, 2, 11, 9, 1, 0),
    )
    scheduler = ReminderScheduler(
        schedule_store,
        reminder_store,
        cron_store=cron_store,
        cron_run_store=cron_run_store,
    )

    first_due = scheduler.collect_due(now=datetime(2026, 2, 11, 9, 1, 0))
    second_due = scheduler.collect_due(now=datetime(2026, 2, 11, 9, 1, 0))

    first_cron = [item for item in first_due if isinstance(item, CronPayload)]
    second_cron = [item for item in second_due if isinstance(item, CronPayload)]

    assert len(first_cron) == 1
    assert second_cron == []
