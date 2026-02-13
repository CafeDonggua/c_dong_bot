from __future__ import annotations

from datetime import datetime

from dongdong_bot.agent.cron_nl_router import CronNLRouter
from dongdong_bot.agent.cron_parser import CronParser
from dongdong_bot.agent.cron_run_store import CronRunStore
from dongdong_bot.agent.cron_service import CronService
from dongdong_bot.agent.cron_store import CronStore
from dongdong_bot.agent.reminder_store import ReminderStore
from dongdong_bot.agent.schedule_store import ScheduleStore
from dongdong_bot.cron.scheduler import CronPayload, ReminderScheduler


def test_nl_repeating_route_creates_task_and_visible_in_list(tmp_path) -> None:
    store = CronStore(str(tmp_path / "cron_tasks.json"))
    service = CronService(store)
    command_parser = CronParser()
    router = CronNLRouter()

    decision = router.route("每天 9 點提醒我喝水", now=datetime(2026, 2, 11, 8, 50, 0))
    assert decision.route_target == "cron_create"
    assert decision.parse_result is not None

    command = service.build_add_command(
        name=decision.parse_result.title,
        message=decision.parse_result.message,
        schedule_kind=decision.parse_result.schedule_kind or "",
        schedule_value=decision.parse_result.schedule_value or "",
    )
    result = service.handle(command, user_id="user-1", chat_id="chat-1", now=datetime(2026, 2, 11, 8, 50, 0))
    assert "已建立 /cron 任務" in result.reply

    list_command = command_parser.parse("/cron list")
    assert list_command is not None
    list_result = service.handle(list_command, user_id="user-1", chat_id="chat-1")
    assert "喝水" in list_result.reply
    assert "cron:0 9 * * *" in list_result.reply


def test_nl_repeating_task_survives_restart_and_can_trigger(tmp_path) -> None:
    schedules_path = str(tmp_path / "schedules.json")
    reminders_path = str(tmp_path / "reminders.json")
    cron_tasks_path = str(tmp_path / "cron_tasks.json")
    cron_runs_path = str(tmp_path / "cron_runs.json")

    store_before = CronStore(cron_tasks_path)
    service = CronService(store_before)
    router = CronNLRouter()

    decision = router.route("每 1 分鐘提醒我喝水", now=datetime(2026, 2, 11, 9, 0, 0))
    assert decision.route_target == "cron_create"
    assert decision.parse_result is not None

    command = service.build_add_command(
        name=decision.parse_result.title,
        message=decision.parse_result.message,
        schedule_kind=decision.parse_result.schedule_kind or "",
        schedule_value=decision.parse_result.schedule_value or "",
    )
    create_result = service.handle(command, user_id="user-1", chat_id="chat-1", now=datetime(2026, 2, 11, 9, 0, 0))
    assert "已建立 /cron 任務" in create_result.reply

    store_after = CronStore(cron_tasks_path)
    scheduler = ReminderScheduler(
        ScheduleStore(schedules_path),
        ReminderStore(reminders_path),
        cron_store=store_after,
        cron_run_store=CronRunStore(cron_runs_path),
    )
    due = scheduler.collect_due(now=datetime(2026, 2, 11, 9, 1, 1))
    cron_due = [item for item in due if isinstance(item, CronPayload)]
    assert len(cron_due) == 1
