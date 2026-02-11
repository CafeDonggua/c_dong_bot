from datetime import datetime

from dongdong_bot.agent.cron_parser import CronParser
from dongdong_bot.agent.cron_service import CronService
from dongdong_bot.agent.cron_store import CronStore


def test_cron_list_shows_required_fields_and_only_owner_tasks(tmp_path):
    store = CronStore(str(tmp_path / "cron_tasks.json"))
    service = CronService(store)
    parser = CronParser()

    store.create(
        owner_user_id="user-1",
        owner_chat_id="chat-1",
        name="晨會提醒",
        message="準備開會",
        schedule_kind="every",
        schedule_value="300",
        next_run_at=datetime(2026, 2, 11, 9, 5),
    )
    store.create(
        owner_user_id="user-2",
        owner_chat_id="chat-2",
        name="他人任務",
        message="不應出現在清單",
        schedule_kind="every",
        schedule_value="60",
        next_run_at=datetime(2026, 2, 11, 9, 1),
    )

    command = parser.parse("/cron list")
    assert command is not None
    result = service.handle(command, user_id="user-1", chat_id="chat-1")

    assert "/cron 任務清單" in result.reply
    assert "晨會提醒" in result.reply
    assert "狀態:scheduled" in result.reply
    assert "下次:2026-02-11 09:05" in result.reply
    assert "他人任務" not in result.reply


def test_cron_list_supports_status_filter(tmp_path):
    store = CronStore(str(tmp_path / "cron_tasks.json"))
    service = CronService(store)
    parser = CronParser()

    active = store.create(
        owner_user_id="user-1",
        owner_chat_id="chat-1",
        name="啟用任務",
        message="active",
        schedule_kind="every",
        schedule_value="60",
        next_run_at=datetime(2026, 2, 11, 9, 1),
    )
    paused = store.create(
        owner_user_id="user-1",
        owner_chat_id="chat-1",
        name="停用任務",
        message="paused",
        schedule_kind="every",
        schedule_value="120",
        next_run_at=datetime(2026, 2, 11, 9, 2),
    )
    store.mark_disabled(paused.task_id, enabled=False)

    command = parser.parse("/cron list paused")
    assert command is not None
    result = service.handle(command, user_id="user-1", chat_id="chat-1")

    assert "停用任務" in result.reply
    assert "啟用任務" not in result.reply
    assert active.task_id[:8] not in result.reply
