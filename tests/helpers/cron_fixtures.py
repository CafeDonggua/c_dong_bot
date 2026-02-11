from __future__ import annotations

from datetime import datetime

from dongdong_bot.agent.cron_models import CronRunRecord, CronTask


def build_cron_task(
    *,
    task_id: str = "task-001",
    owner_user_id: str = "user-1",
    owner_chat_id: str = "chat-1",
    name: str = "每日檢查",
    message: str = "請完成每日檢查",
    schedule_kind: str = "every",
    schedule_value: str = "60",
    enabled: bool = True,
    status: str = "scheduled",
    next_run_at: datetime | None = None,
) -> CronTask:
    now = datetime(2026, 2, 11, 9, 0, 0)
    return CronTask(
        task_id=task_id,
        owner_user_id=owner_user_id,
        owner_chat_id=owner_chat_id,
        name=name,
        message=message,
        schedule_kind=schedule_kind,
        schedule_value=schedule_value,
        enabled=enabled,
        status=status,
        next_run_at=next_run_at or now,
        last_run_at=None,
        last_status=None,
        last_error="",
        created_at=now,
        updated_at=now,
    )


def build_cron_run(
    *,
    run_id: str = "run-001",
    task_id: str = "task-001",
    result: str = "ok",
    error_message: str = "",
    delivery_target: str = "chat-1",
    triggered_at: datetime | None = None,
) -> CronRunRecord:
    now = datetime(2026, 2, 11, 9, 1, 0)
    return CronRunRecord(
        run_id=run_id,
        task_id=task_id,
        triggered_at=triggered_at or now,
        delivery_target=delivery_target,
        result=result,
        error_message=error_message,
    )
