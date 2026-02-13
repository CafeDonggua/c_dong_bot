from __future__ import annotations

from datetime import datetime

from dongdong_bot.agent.cron_nl_router import CronNLRouter
from dongdong_bot.agent.cron_parser import CronParser
from dongdong_bot.agent.cron_service import CronService
from dongdong_bot.agent.cron_store import CronStore


def test_cron_help_and_command_mode_can_coexist(tmp_path) -> None:
    store = CronStore(str(tmp_path / "cron_tasks.json"))
    service = CronService(store)
    command_parser = CronParser()
    nl_router = CronNLRouter()

    help_command = command_parser.parse("/cron help")
    assert help_command is not None
    help_result = service.handle(help_command, user_id="user-1", chat_id="chat-1")
    assert "自然語句範例" in help_result.reply
    assert "/cron add every" in help_result.reply

    nl_decision = nl_router.route("每 30 分鐘提醒站起來", now=datetime(2026, 2, 11, 9, 0, 0))
    assert nl_decision.route_target == "cron_create"
    assert nl_decision.parse_result is not None
    nl_command = service.build_add_command(
        name=nl_decision.parse_result.title,
        message=nl_decision.parse_result.message,
        schedule_kind=nl_decision.parse_result.schedule_kind or "",
        schedule_value=nl_decision.parse_result.schedule_value or "",
    )
    nl_result = service.handle(nl_command, user_id="user-1", chat_id="chat-1", now=datetime(2026, 2, 11, 9, 0, 0))
    assert "已建立 /cron 任務" in nl_result.reply

    command = command_parser.parse("/cron add every 60 喝水提醒 | 請喝水")
    assert command is not None
    cmd_result = service.handle(command, user_id="user-1", chat_id="chat-1", now=datetime(2026, 2, 11, 9, 0, 0))
    assert "已建立 /cron 任務" in cmd_result.reply

    list_command = command_parser.parse("/cron list")
    assert list_command is not None
    list_result = service.handle(list_command, user_id="user-1", chat_id="chat-1")
    assert "站起來" in list_result.reply
    assert "喝水提醒" in list_result.reply
