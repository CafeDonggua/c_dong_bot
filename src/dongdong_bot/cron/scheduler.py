from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from dongdong_bot.agent.reminder_store import ReminderStore, Reminder
from dongdong_bot.agent.schedule_store import ScheduleStore


@dataclass
class ReminderPayload:
    reminder_id: str
    schedule_id: str
    chat_id: str
    message: str


class ReminderScheduler:
    def __init__(self, schedule_store: ScheduleStore, reminder_store: ReminderStore) -> None:
        self.schedule_store = schedule_store
        self.reminder_store = reminder_store

    def collect_due(self, now: Optional[datetime] = None) -> List[ReminderPayload]:
        now = now or datetime.now()
        due: List[ReminderPayload] = []
        for reminder in self.reminder_store.list_pending():
            if reminder.trigger_time > now:
                continue
            schedule = self.schedule_store.get(reminder.schedule_id)
            if schedule is None or schedule.status != "scheduled":
                self.reminder_store.mark_failed(reminder.reminder_id, "schedule_missing")
                continue
            message = f"提醒你：{schedule.title}（{schedule.start_time.strftime('%H:%M')}）"
            due.append(
                ReminderPayload(
                    reminder_id=reminder.reminder_id,
                    schedule_id=schedule.schedule_id,
                    chat_id=schedule.chat_id,
                    message=message,
                )
            )
        return due

    def mark_sent(self, reminder: ReminderPayload) -> None:
        self.reminder_store.mark_sent(reminder.reminder_id)
        self.schedule_store.complete(reminder.schedule_id)

    def mark_failed(self, reminder: ReminderPayload, error: str) -> None:
        self.reminder_store.mark_failed(reminder.reminder_id, error)
