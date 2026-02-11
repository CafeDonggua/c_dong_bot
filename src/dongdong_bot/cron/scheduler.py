from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from dongdong_bot.agent.cron_run_store import CronRunStore
from dongdong_bot.agent.cron_store import CronStore
from dongdong_bot.agent.reminder_store import ReminderStore
from dongdong_bot.agent.schedule_store import ScheduleStore
from dongdong_bot.cron.schedule_rules import next_run_at


@dataclass
class ReminderPayload:
    reminder_id: str
    schedule_id: str
    chat_id: str
    message: str


@dataclass
class CronPayload:
    task_id: str
    chat_id: str
    message: str


class ReminderScheduler:
    def __init__(
        self,
        schedule_store: ScheduleStore,
        reminder_store: ReminderStore,
        cron_store: CronStore | None = None,
        cron_run_store: CronRunStore | None = None,
    ) -> None:
        self.schedule_store = schedule_store
        self.reminder_store = reminder_store
        self.cron_store = cron_store
        self.cron_run_store = cron_run_store
        self._cron_inflight_task_ids: set[str] = set()

    def collect_due(self, now: Optional[datetime] = None) -> List[ReminderPayload | CronPayload]:
        now = now or datetime.now()
        due: List[ReminderPayload | CronPayload] = []
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
        if self.cron_store:
            for task in self.cron_store.list_due(now=now):
                if task.task_id in self._cron_inflight_task_ids:
                    continue
                message = task.message.strip() if task.message.strip() else task.name.strip()
                if not message:
                    message = f"提醒你：{task.name}"
                self._cron_inflight_task_ids.add(task.task_id)
                due.append(
                    CronPayload(
                        task_id=task.task_id,
                        chat_id=task.owner_chat_id,
                        message=message,
                    )
                )
        return due

    def mark_sent(self, reminder: ReminderPayload | CronPayload, now: Optional[datetime] = None) -> None:
        if isinstance(reminder, ReminderPayload):
            self.reminder_store.mark_sent(reminder.reminder_id)
            self.schedule_store.complete(reminder.schedule_id)
            return
        self._cron_inflight_task_ids.discard(reminder.task_id)
        if not self.cron_store:
            return
        current = now or datetime.now()
        task = self.cron_store.get(reminder.task_id)
        if task is None:
            return
        next_time = next_run_at(
            task.schedule_kind,
            task.schedule_value,
            reference_time=current,
            last_run_at=current,
        )
        if next_time is None:
            status = "completed"
        else:
            status = "scheduled"
        self.cron_store.touch_status(
            reminder.task_id,
            status=status,
            next_run_at=next_time,
            last_run_at=current,
            last_status="ok",
            last_error="",
        )
        if self.cron_run_store:
            self.cron_run_store.create(
                task_id=reminder.task_id,
                delivery_target=reminder.chat_id,
                result="ok",
                triggered_at=current,
            )

    def mark_failed(
        self,
        reminder: ReminderPayload | CronPayload,
        error: str,
        now: Optional[datetime] = None,
    ) -> None:
        if isinstance(reminder, ReminderPayload):
            self.reminder_store.mark_failed(reminder.reminder_id, error)
            return
        self._cron_inflight_task_ids.discard(reminder.task_id)
        if not self.cron_store:
            return
        current = now or datetime.now()
        task = self.cron_store.get(reminder.task_id)
        next_time = task.next_run_at if task else None
        self.cron_store.touch_status(
            reminder.task_id,
            status="failed",
            next_run_at=next_time,
            last_run_at=current,
            last_status="error",
            last_error=error,
        )
        if self.cron_run_store:
            self.cron_run_store.create(
                task_id=reminder.task_id,
                delivery_target=reminder.chat_id,
                result="error",
                error_message=error,
                triggered_at=current,
            )
