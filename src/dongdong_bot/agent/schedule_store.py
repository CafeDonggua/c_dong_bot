from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional
import json
from uuid import uuid4


@dataclass
class ScheduleItem:
    schedule_id: str
    user_id: str
    chat_id: str
    title: str
    description: str
    start_time: datetime
    end_time: datetime | None
    timezone: str
    status: str

    def to_dict(self) -> dict:
        return {
            "schedule_id": self.schedule_id,
            "user_id": self.user_id,
            "chat_id": self.chat_id,
            "title": self.title,
            "description": self.description,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "timezone": self.timezone,
            "status": self.status,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ScheduleItem":
        return cls(
            schedule_id=str(data.get("schedule_id", "")),
            user_id=str(data.get("user_id", "")),
            chat_id=str(data.get("chat_id", "")),
            title=str(data.get("title", "")),
            description=str(data.get("description", "")),
            start_time=datetime.fromisoformat(data.get("start_time")),
            end_time=datetime.fromisoformat(data["end_time"]) if data.get("end_time") else None,
            timezone=str(data.get("timezone", "")),
            status=str(data.get("status", "scheduled")),
        )


class ScheduleStore:
    def __init__(self, path: str) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def list(self, user_id: str) -> List[ScheduleItem]:
        return [item for item in self._load() if item.user_id == user_id]

    def get(self, schedule_id: str) -> Optional[ScheduleItem]:
        for item in self._load():
            if item.schedule_id == schedule_id:
                return item
        return None

    def create(
        self,
        user_id: str,
        chat_id: str,
        title: str,
        description: str,
        start_time: datetime,
        end_time: datetime | None,
        timezone: str,
    ) -> ScheduleItem:
        schedule = ScheduleItem(
            schedule_id=uuid4().hex,
            user_id=user_id,
            chat_id=chat_id,
            title=title,
            description=description,
            start_time=start_time,
            end_time=end_time,
            timezone=timezone,
            status="scheduled",
        )
        items = self._load()
        items.append(schedule)
        self._write(items)
        return schedule

    def update(self, schedule_id: str, **fields) -> Optional[ScheduleItem]:
        items = self._load()
        updated = None
        for idx, item in enumerate(items):
            if item.schedule_id != schedule_id:
                continue
            data = item.to_dict()
            for key, value in fields.items():
                if value is None:
                    continue
                if key in {"start_time", "end_time"} and isinstance(value, datetime):
                    data[key] = value.isoformat()
                elif key in data:
                    data[key] = value
            updated = ScheduleItem.from_dict(data)
            items[idx] = updated
            break
        if updated:
            self._write(items)
        return updated

    def cancel(self, schedule_id: str) -> Optional[ScheduleItem]:
        return self.update(schedule_id, status="cancelled")

    def _load(self) -> List[ScheduleItem]:
        if not self.path.exists():
            return []
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return []
        if not isinstance(data, list):
            return []
        items: List[ScheduleItem] = []
        for item in data:
            if not isinstance(item, dict):
                continue
            if not item.get("start_time"):
                continue
            try:
                items.append(ScheduleItem.from_dict(item))
            except (TypeError, ValueError):
                continue
        return items

    def _write(self, items: List[ScheduleItem]) -> None:
        payload = [item.to_dict() for item in items]
        tmp_path = self.path.with_suffix(".tmp")
        tmp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp_path.replace(self.path)
