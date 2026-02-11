from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
from typing import List, Optional
from uuid import uuid4

from dongdong_bot.agent.cron_models import CronRunRecord


class CronRunStore:
    def __init__(self, path: str) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def create(
        self,
        task_id: str,
        delivery_target: str,
        result: str,
        error_message: str = "",
        triggered_at: datetime | None = None,
    ) -> CronRunRecord:
        record = CronRunRecord(
            run_id=uuid4().hex,
            task_id=task_id,
            triggered_at=triggered_at or datetime.now(),
            delivery_target=delivery_target,
            result=result,
            error_message=error_message,
        )
        self.append(record)
        return record

    def append(self, record: CronRunRecord) -> CronRunRecord:
        records = self._load()
        records.append(record)
        self._write(records)
        return record

    def list(self, task_id: str | None = None, limit: int | None = None) -> List[CronRunRecord]:
        records = self._load()
        if task_id is not None:
            records = [record for record in records if record.task_id == task_id]
        records.sort(key=lambda item: item.triggered_at, reverse=True)
        if limit is not None and limit >= 0:
            records = records[:limit]
        return records

    def latest(self, task_id: str) -> Optional[CronRunRecord]:
        records = self.list(task_id=task_id, limit=1)
        return records[0] if records else None

    def _load(self) -> List[CronRunRecord]:
        if not self.path.exists():
            return []
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return []
        if not isinstance(data, list):
            return []
        records: List[CronRunRecord] = []
        for item in data:
            if not isinstance(item, dict):
                continue
            try:
                record = CronRunRecord.from_dict(item)
            except (TypeError, ValueError):
                continue
            if not record.run_id or not record.task_id:
                continue
            records.append(record)
        return records

    def _write(self, records: List[CronRunRecord]) -> None:
        payload = [record.to_dict() for record in records]
        tmp_path = self.path.with_suffix(".tmp")
        tmp_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        tmp_path.replace(self.path)
