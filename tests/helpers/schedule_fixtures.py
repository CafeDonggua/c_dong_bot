from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Tuple

from dongdong_bot.agent.reminder_store import ReminderStore
from dongdong_bot.agent.schedule_store import ScheduleStore, ScheduleItem


def make_stores(tmp_path: Path) -> Tuple[ScheduleStore, ReminderStore]:
    schedule_store = ScheduleStore(str(tmp_path / "schedules.json"))
    reminder_store = ReminderStore(str(tmp_path / "reminders.json"))
    return schedule_store, reminder_store


def create_schedule(
    schedule_store: ScheduleStore,
    *,
    user_id: str = "user-1",
    chat_id: str = "chat-1",
    title: str = "測試行程",
    start_time: datetime | None = None,
) -> ScheduleItem:
    start_time = start_time or datetime(2026, 2, 5, 9, 0)
    return schedule_store.create(
        user_id=user_id,
        chat_id=chat_id,
        title=title,
        description="",
        start_time=start_time,
        end_time=None,
        timezone="",
    )
