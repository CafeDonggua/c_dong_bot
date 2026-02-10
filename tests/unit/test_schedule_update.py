from datetime import datetime
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dongdong_bot.agent.reminder_store import ReminderStore
from dongdong_bot.agent.schedule_parser import ScheduleCommand
from dongdong_bot.agent.schedule_service import ScheduleService
from dongdong_bot.agent.schedule_store import ScheduleStore
from tests.helpers.schedule_fixtures import create_schedule, make_stores


def _force_schedule_ids(schedule_store: ScheduleStore, ids: list[str]) -> None:
    items = schedule_store._load()
    for item, new_id in zip(items, ids):
        item.schedule_id = new_id
    schedule_store._write(items)


def test_update_schedule_with_short_id(tmp_path):
    schedule_store, reminder_store = make_stores(tmp_path)
    service = ScheduleService(schedule_store, reminder_store)

    schedule = create_schedule(schedule_store, title="原本標題")
    reminder_store.create(schedule.schedule_id, schedule.start_time)

    new_time = datetime(2026, 2, 6, 11, 0)
    command = ScheduleCommand(
        action="update",
        title="更新標題",
        start_time=new_time,
        schedule_id=schedule.schedule_id[:8],
    )
    result = service.handle(command, "user-1", "chat-1")

    assert "已更新行程" in result.reply
    updated = schedule_store.get(schedule.schedule_id)
    assert updated is not None
    assert updated.title == "更新標題"
    assert updated.start_time == new_time


def test_update_schedule_requires_unique_prefix(tmp_path):
    schedule_store, reminder_store = make_stores(tmp_path)
    service = ScheduleService(schedule_store, reminder_store)

    first = create_schedule(schedule_store, title="行程一")
    second = create_schedule(schedule_store, title="行程二")

    prefix = "deadbeef"
    _force_schedule_ids(
        schedule_store,
        [f"{prefix}000000000000000000000000000000", f"{prefix}111111111111111111111111111111"],
    )

    command = ScheduleCommand(action="update", title="新標題", schedule_id=prefix)
    result = service.handle(command, "user-1", "chat-1")

    assert "找到多筆行程" in result.reply


@pytest.mark.parametrize(
    "status_action, expected",
    [
        ("complete", "行程已完成，無法修改"),
        ("cancel", "行程已取消，無法修改"),
    ],
)
def test_update_rejects_completed_or_cancelled(tmp_path, status_action, expected):
    schedule_store, reminder_store = make_stores(tmp_path)
    service = ScheduleService(schedule_store, reminder_store)

    schedule = create_schedule(schedule_store)
    if status_action == "complete":
        schedule_store.complete(schedule.schedule_id)
    else:
        schedule_store.cancel(schedule.schedule_id)

    command = ScheduleCommand(action="update", title="新標題", schedule_id=schedule.schedule_id)
    result = service.handle(command, "user-1", "chat-1")

    assert expected in result.reply


def test_update_rejects_empty_fields(tmp_path):
    schedule_store, reminder_store = make_stores(tmp_path)
    service = ScheduleService(schedule_store, reminder_store)

    schedule = create_schedule(schedule_store)

    command = ScheduleCommand(action="update", title="", schedule_id=schedule.schedule_id)
    result = service.handle(command, "user-1", "chat-1")

    assert "請提供要更新的內容" in result.reply


def test_update_reschedules_reminder(tmp_path):
    schedule_store, reminder_store = make_stores(tmp_path)
    service = ScheduleService(schedule_store, reminder_store)

    schedule = create_schedule(schedule_store)
    reminder_store.create(schedule.schedule_id, schedule.start_time)

    new_time = datetime(2026, 2, 6, 10, 0)
    command = ScheduleCommand(
        action="update",
        title="更新標題",
        start_time=new_time,
        schedule_id=schedule.schedule_id,
    )
    result = service.handle(command, "user-1", "chat-1")

    assert "已更新行程" in result.reply

    pending = reminder_store.list_pending()
    assert len(pending) == 1
    assert pending[0].trigger_time == new_time

    all_reminders = reminder_store._load()
    failed = [item for item in all_reminders if item.status == "failed"]
    assert failed
    assert failed[0].last_error == "schedule_updated"
