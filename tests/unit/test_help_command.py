from __future__ import annotations

from dongdong_bot.main import _help_text


def test_help_text_lists_core_commands() -> None:
    content = _help_text()
    assert "/help" in content
    assert "/search <關鍵字>" in content
    assert "/summary <網址>" in content
    assert "/cron help" in content
    assert "每天 9 點提醒我喝水" in content
    assert "/skill list" in content
    assert "/allowlist list" in content
