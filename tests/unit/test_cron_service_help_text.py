from __future__ import annotations

from dongdong_bot.agent.cron_parser import CronParser
from dongdong_bot.agent.cron_service import CronService
from dongdong_bot.agent.cron_store import CronStore


def test_cron_help_contains_command_and_natural_language_examples(tmp_path) -> None:
    service = CronService(CronStore(str(tmp_path / "cron_tasks.json")))
    parser = CronParser()
    command = parser.parse("/cron help")
    assert command is not None

    result = service.handle(command, user_id="user-1", chat_id="chat-1")

    assert "/cron add every" in result.reply
    assert "/cron add at" in result.reply
    assert "自然語句範例" in result.reply
    assert "每天 9 點提醒我喝水" in result.reply
