from __future__ import annotations

from dongdong_bot.agent.cron_parser import CronParser
from dongdong_bot.agent.cron_service import CronService
from dongdong_bot.agent.cron_store import CronStore


def test_cron_error_includes_remove_example(tmp_path) -> None:
    parser = CronParser()
    service = CronService(CronStore(str(tmp_path / "cron_tasks.json")))
    command = parser.parse("/cron remove !!")
    assert command is not None

    result = service.handle(command, user_id="user-1", chat_id="chat-1")

    assert "task_id 格式不正確" in result.reply
    assert "例如：/cron remove abcd1234" in result.reply


def test_cron_error_includes_add_example(tmp_path) -> None:
    parser = CronParser()
    service = CronService(CronStore(str(tmp_path / "cron_tasks.json")))
    command = parser.parse("/cron add")
    assert command is not None

    result = service.handle(command, user_id="user-1", chat_id="chat-1")

    assert "缺少排程型態或排程值" in result.reply
    assert "例如：/cron add every 60 喝水提醒 | 請喝水" in result.reply


def test_cron_error_includes_help_example_for_unknown_subcommand(tmp_path) -> None:
    parser = CronParser()
    service = CronService(CronStore(str(tmp_path / "cron_tasks.json")))
    command = parser.parse("/cron foo")
    assert command is not None

    result = service.handle(command, user_id="user-1", chat_id="chat-1")

    assert "不支援的 /cron 子命令" in result.reply
    assert "例如：/cron help" in result.reply
