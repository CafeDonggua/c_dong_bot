from datetime import datetime

from dongdong_bot.agent.cron_parser import CronParser
from dongdong_bot.agent.cron_service import CronService
from dongdong_bot.agent.cron_store import CronStore


def test_cron_management_blocks_cross_user_operations(tmp_path):
    store = CronStore(str(tmp_path / "cron_tasks.json"))
    service = CronService(store)
    parser = CronParser()

    owner_task = store.create(
        owner_user_id="user-1",
        owner_chat_id="chat-1",
        name="User1 任務",
        message="owner",
        schedule_kind="every",
        schedule_value="60",
        next_run_at=datetime(2026, 2, 11, 9, 1),
    )

    disable_cmd = parser.parse(f"/cron disable {owner_task.task_id[:8]}")
    assert disable_cmd is not None
    disable_result = service.handle(disable_cmd, user_id="user-2", chat_id="chat-2")
    assert "找不到任務" in disable_result.reply

    remove_cmd = parser.parse(f"/cron remove {owner_task.task_id[:8]}")
    assert remove_cmd is not None
    remove_result = service.handle(remove_cmd, user_id="user-2", chat_id="chat-2")
    assert "找不到任務" in remove_result.reply

    unchanged = store.get(owner_task.task_id)
    assert unchanged is not None
    assert unchanged.enabled is True
    assert unchanged.status == "scheduled"


def test_cron_list_only_returns_current_user_tasks(tmp_path):
    store = CronStore(str(tmp_path / "cron_tasks.json"))
    service = CronService(store)
    parser = CronParser()

    store.create(
        owner_user_id="user-1",
        owner_chat_id="chat-1",
        name="User1 任務",
        message="owner",
        schedule_kind="every",
        schedule_value="60",
        next_run_at=datetime(2026, 2, 11, 9, 1),
    )
    store.create(
        owner_user_id="user-2",
        owner_chat_id="chat-2",
        name="User2 任務",
        message="other",
        schedule_kind="every",
        schedule_value="120",
        next_run_at=datetime(2026, 2, 11, 9, 2),
    )

    list_cmd = parser.parse("/cron list")
    assert list_cmd is not None
    result = service.handle(list_cmd, user_id="user-1", chat_id="chat-1")

    assert "User1 任務" in result.reply
    assert "User2 任務" not in result.reply
