from dongdong_bot.agent.cron_parser import CronParser


def test_cron_add_every_parses_name_and_message():
    parser = CronParser()

    command = parser.parse("/cron add every 60 每分鐘喝水 | 請喝一口水")

    assert command is not None
    assert command.valid
    assert command.action == "add"
    assert command.schedule_kind == "every"
    assert command.schedule_value == "60"
    assert command.name == "每分鐘喝水"
    assert command.message == "請喝一口水"


def test_cron_add_at_parses_iso_time():
    parser = CronParser()

    command = parser.parse("/cron add at 2026-02-11T09:30 開會提醒")

    assert command is not None
    assert command.valid
    assert command.schedule_kind == "at"
    assert command.schedule_value == "2026-02-11T09:30:00"
    assert command.name == "開會提醒"
    assert command.message == "開會提醒"


def test_cron_add_at_accepts_space_separated_datetime():
    parser = CronParser()

    command = parser.parse("/cron add at 2026-02-11 23:50 單次提醒 | 23:50 開會")

    assert command is not None
    assert command.valid
    assert command.schedule_kind == "at"
    assert command.schedule_value == "2026-02-11T23:50:00"
    assert command.name == "單次提醒"
    assert command.message == "23:50 開會"


def test_cron_add_parses_quoted_cron_expression():
    parser = CronParser()

    command = parser.parse('/cron add cron "*/5 * * * *" 站立提醒 | 起來活動')

    assert command is not None
    assert command.valid
    assert command.schedule_kind == "cron"
    assert command.schedule_value == "*/5 * * * *"
    assert command.name == "站立提醒"
    assert command.message == "起來活動"


def test_cron_add_rejects_invalid_schedule_and_missing_name():
    parser = CronParser()

    invalid_kind = parser.parse("/cron add weekly 10 無效任務")
    missing_name = parser.parse("/cron add every 60")

    assert invalid_kind is not None
    assert not invalid_kind.valid
    assert "不支援的排程型態" in invalid_kind.errors[0]

    assert missing_name is not None
    assert not missing_name.valid
    assert "缺少排程型態或排程值" not in missing_name.errors[0]
    assert "缺少任務名稱" in missing_name.errors[0]
