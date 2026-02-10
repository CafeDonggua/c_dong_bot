from datetime import datetime

from dongdong_bot.agent.schedule_parser import ScheduleParser


def test_relative_time_tomorrow():
    parser = ScheduleParser()
    now = datetime(2026, 2, 5, 9, 0)
    command = parser.parse("提醒我明天 10:30 開會", now=now)
    assert command is not None
    assert command.start_time == datetime(2026, 2, 6, 10, 30)


def test_relative_time_day_after_tomorrow():
    parser = ScheduleParser()
    now = datetime(2026, 2, 5, 9, 0)
    command = parser.parse("後天早上9點提醒我上班", now=now)
    assert command is not None
    assert command.start_time == datetime(2026, 2, 7, 9, 0)


def test_relative_time_afternoon():
    parser = ScheduleParser()
    now = datetime(2026, 2, 5, 9, 0)
    command = parser.parse("明天下午3點提醒我報告", now=now)
    assert command is not None
    assert command.start_time == datetime(2026, 2, 6, 15, 0)
