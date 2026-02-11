from __future__ import annotations

from dongdong_bot.channels.telegram import TelegramClient


def test_command_registry_includes_cron() -> None:
    assert "cron" in TelegramClient.COMMAND_NAMES


def test_command_registry_includes_help() -> None:
    assert "help" in TelegramClient.COMMAND_NAMES
