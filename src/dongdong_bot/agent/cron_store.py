from __future__ import annotations

from dataclasses import replace
from datetime import datetime
import json
from pathlib import Path
from typing import Any, List, Optional
from uuid import uuid4

from dongdong_bot.agent.cron_models import CronTask


class CronStore:
    def __init__(self, path: str) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def list(
        self,
        owner_user_id: str | None = None,
        status: str | None = None,
        enabled: bool | None = None,
    ) -> List[CronTask]:
        items = self._load()
        if owner_user_id is not None:
            items = [item for item in items if item.owner_user_id == owner_user_id]
        if status is not None:
            items = [item for item in items if item.status == status]
        if enabled is not None:
            items = [item for item in items if item.enabled == enabled]
        return items

    def list_due(self, now: datetime | None = None) -> List[CronTask]:
        current = now or datetime.now()
        due: List[CronTask] = []
        for task in self._load():
            if not task.enabled or task.status != "scheduled":
                continue
            if task.next_run_at and task.next_run_at <= current:
                due.append(task)
        return due

    def get(self, task_id: str) -> Optional[CronTask]:
        for item in self._load():
            if item.task_id == task_id:
                return item
        return None

    def resolve_for_owner(self, owner_user_id: str, task_id_prefix: str) -> tuple[Optional[CronTask], str | None]:
        matches = [
            item
            for item in self.list(owner_user_id=owner_user_id)
            if item.task_id.startswith(task_id_prefix)
        ]
        if not matches:
            return None, "找不到任務。"
        if len(matches) > 1:
            return None, "找到多筆任務符合此 ID，請提供更完整的 ID。"
        return matches[0], None

    def create(
        self,
        owner_user_id: str,
        owner_chat_id: str,
        name: str,
        message: str,
        schedule_kind: str,
        schedule_value: str,
        next_run_at: datetime | None,
    ) -> CronTask:
        now = datetime.now()
        task = CronTask(
            task_id=self._new_task_id(),
            owner_user_id=owner_user_id,
            owner_chat_id=owner_chat_id,
            name=name,
            message=message,
            schedule_kind=schedule_kind,
            schedule_value=schedule_value,
            enabled=True,
            status="scheduled",
            next_run_at=next_run_at,
            last_run_at=None,
            last_status=None,
            last_error="",
            created_at=now,
            updated_at=now,
        )
        items = self._load()
        items.append(task)
        self._write(items)
        return task

    def add(self, task: CronTask) -> CronTask:
        items = self._load()
        if any(item.task_id == task.task_id for item in items):
            raise ValueError(f"task_id already exists: {task.task_id}")
        items.append(task)
        self._write(items)
        return task

    def update(self, task_id: str, **fields: Any) -> Optional[CronTask]:
        items = self._load()
        updated: Optional[CronTask] = None
        for index, item in enumerate(items):
            if item.task_id != task_id:
                continue
            payload = item.to_dict()
            for key, value in fields.items():
                if key not in payload:
                    continue
                if isinstance(value, datetime):
                    payload[key] = value.isoformat()
                else:
                    payload[key] = value
            if "updated_at" not in fields:
                payload["updated_at"] = datetime.now().isoformat()
            updated = CronTask.from_dict(payload)
            items[index] = updated
            break
        if updated is not None:
            self._write(items)
        return updated

    def touch_status(
        self,
        task_id: str,
        *,
        status: str,
        next_run_at: datetime | None,
        last_run_at: datetime | None = None,
        last_status: str | None = None,
        last_error: str = "",
    ) -> Optional[CronTask]:
        return self.update(
            task_id,
            status=status,
            next_run_at=next_run_at,
            last_run_at=last_run_at,
            last_status=last_status,
            last_error=last_error,
        )

    def mark_disabled(self, task_id: str, enabled: bool) -> Optional[CronTask]:
        status = "scheduled" if enabled else "paused"
        return self.update(task_id, enabled=enabled, status=status)

    def mark_disabled_for_owner(
        self,
        owner_user_id: str,
        task_id_prefix: str,
        enabled: bool,
    ) -> tuple[Optional[CronTask], str | None]:
        task, error = self.resolve_for_owner(owner_user_id, task_id_prefix)
        if error:
            return None, error
        if task is None:
            return None, "找不到任務。"
        updated = self.mark_disabled(task.task_id, enabled=enabled)
        return updated, None

    def remove(self, task_id: str) -> bool:
        items = self._load()
        kept: List[CronTask] = []
        deleted = False
        for item in items:
            if item.task_id == task_id:
                deleted = True
                continue
            kept.append(item)
        if deleted:
            self._write(kept)
        return deleted

    def remove_for_owner(self, owner_user_id: str, task_id_prefix: str) -> tuple[bool, str | None]:
        task, error = self.resolve_for_owner(owner_user_id, task_id_prefix)
        if error:
            return False, error
        if task is None:
            return False, "找不到任務。"
        return self.remove(task.task_id), None

    def upsert(self, task: CronTask) -> CronTask:
        items = self._load()
        for index, item in enumerate(items):
            if item.task_id != task.task_id:
                continue
            items[index] = replace(task, updated_at=datetime.now())
            self._write(items)
            return items[index]
        items.append(task)
        self._write(items)
        return task

    def _new_task_id(self) -> str:
        known = {item.task_id for item in self._load()}
        while True:
            candidate = uuid4().hex[:12]
            if candidate not in known:
                return candidate

    def _load(self) -> List[CronTask]:
        if not self.path.exists():
            return []
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return []
        if not isinstance(data, list):
            return []
        tasks: List[CronTask] = []
        for item in data:
            if not isinstance(item, dict):
                continue
            try:
                task = CronTask.from_dict(item)
            except (TypeError, ValueError):
                continue
            if not task.task_id or not task.owner_user_id:
                continue
            tasks.append(task)
        return tasks

    def _write(self, tasks: List[CronTask]) -> None:
        payload = [task.to_dict() for task in tasks]
        tmp_path = self.path.with_suffix(".tmp")
        tmp_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        tmp_path.replace(self.path)
