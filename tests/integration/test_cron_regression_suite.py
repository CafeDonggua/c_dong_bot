from __future__ import annotations

from datetime import datetime
from types import SimpleNamespace

from dongdong_bot.agent.cron_nl_router import CronNLRouter
from dongdong_bot.agent.cron_parser import CronParser
from dongdong_bot.agent.cron_run_store import CronRunStore
from dongdong_bot.agent.cron_service import CronService
from dongdong_bot.agent.cron_store import CronStore
from dongdong_bot.agent.reminder_store import ReminderStore
from dongdong_bot.agent.schedule_store import ScheduleStore
from dongdong_bot.cron.scheduler import CronPayload, ReminderScheduler
from dongdong_bot.main import _recover_cron_tasks


def test_cron_regression_add_manage_and_trigger_flow(tmp_path):
    cron_store = CronStore(str(tmp_path / "cron_tasks.json"))
    cron_run_store = CronRunStore(str(tmp_path / "cron_runs.json"))
    schedule_store = ScheduleStore(str(tmp_path / "schedules.json"))
    reminder_store = ReminderStore(str(tmp_path / "reminders.json"))
    parser = CronParser()
    service = CronService(cron_store)
    scheduler = ReminderScheduler(
        schedule_store,
        reminder_store,
        cron_store=cron_store,
        cron_run_store=cron_run_store,
    )

    add_cmd = parser.parse("/cron add every 60 每分鐘喝水 | 喝水囉")
    assert add_cmd is not None
    add_result = service.handle(add_cmd, user_id="user-1", chat_id="chat-1", now=datetime(2026, 2, 11, 9, 0, 0))
    assert "已建立 /cron 任務" in add_result.reply

    tasks = cron_store.list(owner_user_id="user-1")
    assert len(tasks) == 1
    task_id_prefix = tasks[0].task_id[:8]

    list_cmd = parser.parse("/cron list")
    assert list_cmd is not None
    list_result = service.handle(list_cmd, user_id="user-1", chat_id="chat-1")
    assert "每分鐘喝水" in list_result.reply

    disable_cmd = parser.parse(f"/cron disable {task_id_prefix}")
    assert disable_cmd is not None
    disable_result = service.handle(disable_cmd, user_id="user-1", chat_id="chat-1")
    assert "已停用任務" in disable_result.reply

    enable_cmd = parser.parse(f"/cron enable {task_id_prefix}")
    assert enable_cmd is not None
    enable_result = service.handle(enable_cmd, user_id="user-1", chat_id="chat-1", now=datetime(2026, 2, 11, 9, 1, 0))
    assert "已啟用任務" in enable_result.reply

    due = scheduler.collect_due(now=datetime(2026, 2, 11, 9, 2, 0))
    cron_due = [item for item in due if isinstance(item, CronPayload)]
    assert len(cron_due) == 1
    scheduler.mark_sent(cron_due[0], now=datetime(2026, 2, 11, 9, 2, 0))

    latest = cron_run_store.latest(tasks[0].task_id)
    assert latest is not None
    assert latest.result == "ok"


def test_cron_regression_restart_recovery_and_owner_isolation(tmp_path):
    cron_store = CronStore(str(tmp_path / "cron_tasks.json"))
    cron_run_store = CronRunStore(str(tmp_path / "cron_runs.json"))
    schedule_store = ScheduleStore(str(tmp_path / "schedules.json"))
    reminder_store = ReminderStore(str(tmp_path / "reminders.json"))
    parser = CronParser()
    service = CronService(cron_store)
    scheduler = ReminderScheduler(
        schedule_store,
        reminder_store,
        cron_store=cron_store,
        cron_run_store=cron_run_store,
    )

    task = cron_store.create(
        owner_user_id="user-1",
        owner_chat_id="chat-1",
        name="重啟恢復任務",
        message="重啟後要可觸發",
        schedule_kind="every",
        schedule_value="60",
        next_run_at=datetime(2026, 2, 11, 9, 1, 0),
    )
    cron_store.touch_status(
        task.task_id,
        status="scheduled",
        next_run_at=None,
        last_run_at=datetime(2026, 2, 11, 9, 0, 0),
    )
    _recover_cron_tasks(cron_store, SimpleNamespace(info=lambda *_: None), now=datetime(2026, 2, 11, 9, 1, 0))

    recovered = cron_store.get(task.task_id)
    assert recovered is not None
    assert recovered.next_run_at is not None
    assert recovered.status == "scheduled"

    remove_cmd = parser.parse(f"/cron remove {task.task_id[:8]}")
    assert remove_cmd is not None
    blocked = service.handle(remove_cmd, user_id="user-2", chat_id="chat-2")
    assert "找不到任務" in blocked.reply

    due = scheduler.collect_due(now=datetime(2026, 2, 11, 9, 2, 0))
    cron_due = [item for item in due if isinstance(item, CronPayload)]
    assert cron_due


def test_cron_regression_nl_route_and_command_contract(tmp_path):
    cron_store = CronStore(str(tmp_path / "cron_tasks.json"))
    parser = CronParser()
    service = CronService(cron_store)
    nl_router = CronNLRouter()

    decision = nl_router.route("每天 9 點提醒我喝水", now=datetime(2026, 2, 11, 8, 50, 0))
    assert decision.route_target == "cron_create"
    assert decision.parse_result is not None
    add_command = service.build_add_command(
        name=decision.parse_result.title,
        message=decision.parse_result.message,
        schedule_kind=decision.parse_result.schedule_kind or "",
        schedule_value=decision.parse_result.schedule_value or "",
    )
    create_result = service.handle(add_command, user_id="user-1", chat_id="chat-1", now=datetime(2026, 2, 11, 8, 50, 0))
    assert "已建立 /cron 任務" in create_result.reply

    command_add = parser.parse("/cron add every 60 站立提醒 | 起來動一動")
    assert command_add is not None
    command_result = service.handle(command_add, user_id="user-1", chat_id="chat-1", now=datetime(2026, 2, 11, 8, 50, 0))
    assert "已建立 /cron 任務" in command_result.reply

    list_cmd = parser.parse("/cron list")
    assert list_cmd is not None
    list_result = service.handle(list_cmd, user_id="user-1", chat_id="chat-1")
    assert "喝水" in list_result.reply
    assert "站立提醒" in list_result.reply
