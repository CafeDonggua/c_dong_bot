from datetime import datetime

from dongdong_bot.agent.cron_parser import CronParser
from dongdong_bot.agent.cron_service import CronService
from dongdong_bot.agent.cron_store import CronStore


def test_cron_service_add_creates_task_and_returns_task_id(tmp_path):
    store = CronStore(str(tmp_path / "cron_tasks.json"))
    service = CronService(store)
    parser = CronParser()

    command = parser.parse("/cron add every 60 喝水提醒 | 請喝水")
    assert command is not None
    result = service.handle(command, user_id="user-1", chat_id="chat-1", now=datetime(2026, 2, 11, 9, 0))

    assert "已建立 /cron 任務" in result.reply
    assert "ID:" in result.reply

    tasks = store.list(owner_user_id="user-1")
    assert len(tasks) == 1
    assert tasks[0].name == "喝水提醒"
    assert tasks[0].message == "請喝水"
    assert tasks[0].schedule_kind == "every"
    assert tasks[0].schedule_value == "60"
    assert tasks[0].status == "scheduled"
    assert tasks[0].next_run_at == datetime(2026, 2, 11, 9, 1)


def test_cron_service_add_rejects_past_at_schedule(tmp_path):
    store = CronStore(str(tmp_path / "cron_tasks.json"))
    service = CronService(store)
    parser = CronParser()

    command = parser.parse("/cron add at 2026-02-11T08:00 過期任務")
    assert command is not None
    result = service.handle(command, user_id="user-1", chat_id="chat-1", now=datetime(2026, 2, 11, 9, 0))

    assert "排程時間已過" in result.reply
    assert store.list(owner_user_id="user-1") == []
