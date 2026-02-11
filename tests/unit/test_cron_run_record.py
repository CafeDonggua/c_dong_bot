from datetime import datetime

from dongdong_bot.agent.cron_run_store import CronRunStore
from dongdong_bot.agent.cron_store import CronStore
from dongdong_bot.agent.reminder_store import ReminderStore
from dongdong_bot.agent.schedule_store import ScheduleStore
from dongdong_bot.cron.scheduler import CronPayload, ReminderScheduler


def test_cron_failure_updates_last_error_and_writes_run_record(tmp_path):
    schedule_store = ScheduleStore(str(tmp_path / "schedules.json"))
    reminder_store = ReminderStore(str(tmp_path / "reminders.json"))
    cron_store = CronStore(str(tmp_path / "cron_tasks.json"))
    cron_run_store = CronRunStore(str(tmp_path / "cron_runs.json"))

    task = cron_store.create(
        owner_user_id="user-1",
        owner_chat_id="chat-1",
        name="失敗任務",
        message="會失敗",
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
    payload = CronPayload(task_id=task.task_id, chat_id=task.owner_chat_id, message=task.message)
    scheduler.mark_failed(payload, "network_error", now=datetime(2026, 2, 11, 9, 1, 5))

    updated = cron_store.get(task.task_id)
    assert updated is not None
    assert updated.status == "failed"
    assert updated.last_status == "error"
    assert updated.last_error == "network_error"

    latest = cron_run_store.latest(task.task_id)
    assert latest is not None
    assert latest.result == "error"
    assert latest.error_message == "network_error"


def test_cron_success_clears_last_error_and_writes_success_record(tmp_path):
    schedule_store = ScheduleStore(str(tmp_path / "schedules.json"))
    reminder_store = ReminderStore(str(tmp_path / "reminders.json"))
    cron_store = CronStore(str(tmp_path / "cron_tasks.json"))
    cron_run_store = CronRunStore(str(tmp_path / "cron_runs.json"))

    task = cron_store.create(
        owner_user_id="user-1",
        owner_chat_id="chat-1",
        name="成功任務",
        message="會成功",
        schedule_kind="at",
        schedule_value=datetime(2026, 2, 11, 9, 1, 0).isoformat(),
        next_run_at=datetime(2026, 2, 11, 9, 1, 0),
    )
    cron_store.touch_status(
        task.task_id,
        status="failed",
        next_run_at=datetime(2026, 2, 11, 9, 1, 0),
        last_status="error",
        last_error="old_error",
    )

    scheduler = ReminderScheduler(
        schedule_store,
        reminder_store,
        cron_store=cron_store,
        cron_run_store=cron_run_store,
    )
    payload = CronPayload(task_id=task.task_id, chat_id=task.owner_chat_id, message=task.message)
    scheduler.mark_sent(payload, now=datetime(2026, 2, 11, 9, 1, 0))

    updated = cron_store.get(task.task_id)
    assert updated is not None
    assert updated.last_status == "ok"
    assert updated.last_error == ""
    assert updated.status == "completed"

    latest = cron_run_store.latest(task.task_id)
    assert latest is not None
    assert latest.result == "ok"
    assert latest.error_message == ""
