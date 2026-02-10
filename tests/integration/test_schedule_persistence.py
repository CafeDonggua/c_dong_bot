from datetime import datetime

from dongdong_bot.agent.schedule_store import ScheduleStore


def test_schedule_persistence(tmp_path):
    path = tmp_path / "schedules.json"
    store = ScheduleStore(str(path))

    schedule = store.create(
        user_id="user-1",
        chat_id="chat-1",
        title="測試行程",
        description="",
        start_time=datetime(2026, 2, 5, 9, 0),
        end_time=None,
        timezone="",
    )

    reloaded = ScheduleStore(str(path))
    items = reloaded.list("user-1")

    assert len(items) == 1
    assert items[0].schedule_id == schedule.schedule_id
    assert items[0].title == "測試行程"
