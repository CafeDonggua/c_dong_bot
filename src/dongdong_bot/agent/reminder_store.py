from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional
import json
from uuid import uuid4


@dataclass
class Reminder:
    reminder_id: str
    schedule_id: str
    trigger_time: datetime
    status: str
    last_error: str

    def to_dict(self) -> dict:
        return {
            "reminder_id": self.reminder_id,
            "schedule_id": self.schedule_id,
            "trigger_time": self.trigger_time.isoformat(),
            "status": self.status,
            "last_error": self.last_error,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Reminder":
        return cls(
            reminder_id=str(data.get("reminder_id", "")),
            schedule_id=str(data.get("schedule_id", "")),
            trigger_time=datetime.fromisoformat(data.get("trigger_time")),
            status=str(data.get("status", "pending")),
            last_error=str(data.get("last_error", "")),
        )


class ReminderStore:
    def __init__(self, path: str) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def list_pending(self) -> List[Reminder]:
        return [reminder for reminder in self._load() if reminder.status == "pending"]

    def create(self, schedule_id: str, trigger_time: datetime) -> Reminder:
        reminder = Reminder(
            reminder_id=uuid4().hex,
            schedule_id=schedule_id,
            trigger_time=trigger_time,
            status="pending",
            last_error="",
        )
        reminders = self._load()
        reminders.append(reminder)
        self._write(reminders)
        return reminder

    def mark_sent(self, reminder_id: str) -> None:
        self._update_status(reminder_id, "sent")

    def mark_failed(self, reminder_id: str, error: str) -> None:
        self._update_status(reminder_id, "failed", error)

    def invalidate_pending_by_schedule(self, schedule_id: str, reason: str = "schedule_updated") -> int:
        reminders = self._load()
        updated = 0
        for idx, reminder in enumerate(reminders):
            if reminder.schedule_id != schedule_id or reminder.status != "pending":
                continue
            data = reminder.to_dict()
            data["status"] = "failed"
            data["last_error"] = reason
            reminders[idx] = Reminder.from_dict(data)
            updated += 1
        if updated:
            self._write(reminders)
        return updated

    def _update_status(self, reminder_id: str, status: str, error: str = "") -> None:
        reminders = self._load()
        for idx, reminder in enumerate(reminders):
            if reminder.reminder_id != reminder_id:
                continue
            data = reminder.to_dict()
            data["status"] = status
            data["last_error"] = error
            reminders[idx] = Reminder.from_dict(data)
            break
        self._write(reminders)

    def _load(self) -> List[Reminder]:
        if not self.path.exists():
            return []
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return []
        if not isinstance(data, list):
            return []
        reminders: List[Reminder] = []
        for item in data:
            if not isinstance(item, dict):
                continue
            if not item.get("trigger_time"):
                continue
            try:
                reminders.append(Reminder.from_dict(item))
            except (TypeError, ValueError):
                continue
        return reminders

    def _write(self, reminders: List[Reminder]) -> None:
        payload = [reminder.to_dict() for reminder in reminders]
        tmp_path = self.path.with_suffix(".tmp")
        tmp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp_path.replace(self.path)
