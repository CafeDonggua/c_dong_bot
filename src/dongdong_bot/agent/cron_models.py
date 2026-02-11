from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


TASK_STATUSES = {"scheduled", "paused", "completed", "failed"}
RUN_STATUSES = {"ok", "error"}


def _parse_datetime(value: Any) -> datetime | None:
    if value in (None, ""):
        return None
    try:
        return datetime.fromisoformat(str(value))
    except (TypeError, ValueError):
        return None


def _normalize_task_status(value: Any) -> str:
    status = str(value or "scheduled")
    return status if status in TASK_STATUSES else "scheduled"


def _normalize_run_status(value: Any) -> str:
    status = str(value or "ok")
    return status if status in RUN_STATUSES else "ok"


def _normalize_bool(value: Any, default: bool = True) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "on"}:
        return True
    if text in {"0", "false", "no", "off"}:
        return False
    return default


@dataclass
class CronTask:
    task_id: str
    owner_user_id: str
    owner_chat_id: str
    name: str
    message: str
    schedule_kind: str
    schedule_value: str
    enabled: bool
    status: str
    next_run_at: datetime | None
    last_run_at: datetime | None
    last_status: str | None
    last_error: str
    created_at: datetime
    updated_at: datetime

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "owner_user_id": self.owner_user_id,
            "owner_chat_id": self.owner_chat_id,
            "name": self.name,
            "message": self.message,
            "schedule_kind": self.schedule_kind,
            "schedule_value": self.schedule_value,
            "enabled": self.enabled,
            "status": self.status,
            "next_run_at": self.next_run_at.isoformat() if self.next_run_at else None,
            "last_run_at": self.last_run_at.isoformat() if self.last_run_at else None,
            "last_status": self.last_status,
            "last_error": self.last_error,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CronTask":
        now = datetime.now()
        last_status_raw = str(data.get("last_status", "")).strip()
        last_status = _normalize_run_status(last_status_raw) if last_status_raw else None
        return cls(
            task_id=str(data.get("task_id", "")),
            owner_user_id=str(data.get("owner_user_id", "")),
            owner_chat_id=str(data.get("owner_chat_id", "")),
            name=str(data.get("name", "")),
            message=str(data.get("message", "")),
            schedule_kind=str(data.get("schedule_kind", "")).lower(),
            schedule_value=str(data.get("schedule_value", "")),
            enabled=_normalize_bool(data.get("enabled"), default=True),
            status=_normalize_task_status(data.get("status")),
            next_run_at=_parse_datetime(data.get("next_run_at")),
            last_run_at=_parse_datetime(data.get("last_run_at")),
            last_status=last_status,
            last_error=str(data.get("last_error", "")),
            created_at=_parse_datetime(data.get("created_at")) or now,
            updated_at=_parse_datetime(data.get("updated_at")) or now,
        )


@dataclass
class CronRunRecord:
    run_id: str
    task_id: str
    triggered_at: datetime
    delivery_target: str
    result: str
    error_message: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "task_id": self.task_id,
            "triggered_at": self.triggered_at.isoformat(),
            "delivery_target": self.delivery_target,
            "result": self.result,
            "error_message": self.error_message,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CronRunRecord":
        return cls(
            run_id=str(data.get("run_id", "")),
            task_id=str(data.get("task_id", "")),
            triggered_at=_parse_datetime(data.get("triggered_at")) or datetime.now(),
            delivery_target=str(data.get("delivery_target", "")),
            result=_normalize_run_status(data.get("result")),
            error_message=str(data.get("error_message", "")),
        )
