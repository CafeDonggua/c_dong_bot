from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List

from dongdong_bot.agent.reminder_store import ReminderStore
from dongdong_bot.agent.schedule_parser import ScheduleCommand
from dongdong_bot.agent.schedule_store import ScheduleItem, ScheduleStore


@dataclass
class ScheduleResult:
    reply: str


class ScheduleService:
    def __init__(self, schedule_store: ScheduleStore, reminder_store: ReminderStore) -> None:
        self.schedule_store = schedule_store
        self.reminder_store = reminder_store

    def handle(self, command: ScheduleCommand, user_id: str, chat_id: str) -> ScheduleResult:
        if command.intent == "invalid" and command.message:
            return ScheduleResult(reply=command.message)
        if command.action == "clarify":
            return ScheduleResult(reply=command.message or "請問要刪除還是標示完成？")
        if command.action == "list":
            items = self.schedule_store.list(user_id)
            return ScheduleResult(reply=self._format_list(items, command.list_range))
        if command.action == "add" and command.start_time:
            schedule = self.schedule_store.create(
                user_id=user_id,
                chat_id=chat_id,
                title=command.title,
                description="",
                start_time=command.start_time,
                end_time=None,
                timezone="",
            )
            self.reminder_store.create(schedule.schedule_id, schedule.start_time)
            return ScheduleResult(reply=self._format_created(schedule))
        if command.action == "update" and command.schedule_id:
            updated = self.schedule_store.update(
                command.schedule_id,
                title=command.title or None,
                start_time=command.start_time,
            )
            if updated and command.start_time:
                self.reminder_store.create(updated.schedule_id, updated.start_time)
            return ScheduleResult(reply=self._format_updated(updated))
        if command.action == "delete":
            if not command.schedule_id:
                return ScheduleResult(reply="請先提供行程 ID，可先查詢行程清單。")
            current, resolve_error = self._resolve_schedule(user_id, command.schedule_id)
            if resolve_error:
                return ScheduleResult(reply=resolve_error)
            if current.status == "cancelled":
                return ScheduleResult(reply="行程已取消，無需重複操作。")
            if current.status == "completed":
                return ScheduleResult(reply="行程已完成，無法取消。")
            cancelled = self.schedule_store.cancel(current.schedule_id)
            return ScheduleResult(reply=self._format_deleted(cancelled))
        if command.action == "complete":
            if not command.schedule_id:
                return ScheduleResult(reply="請先提供行程 ID，可先查詢行程清單。")
            current, resolve_error = self._resolve_schedule(user_id, command.schedule_id)
            if resolve_error:
                return ScheduleResult(reply=resolve_error.replace("刪除", "完成"))
            if current.status == "completed":
                return ScheduleResult(reply="行程已完成，無需重複操作。")
            if current.status == "cancelled":
                return ScheduleResult(reply="行程已取消，無法標示完成。")
            completed = self.schedule_store.complete(current.schedule_id)
            return ScheduleResult(reply=self._format_completed(completed))
        return ScheduleResult(reply="我沒看懂行程指令，請提供日期時間，例如：幫我記錄明天 10:00 開會")

    @staticmethod
    def _format_list(items: List[ScheduleItem], list_range: str = "default") -> str:
        if list_range == "completed":
            completed_items = [item for item in items if item.status == "completed"]
            if not completed_items:
                return "目前沒有已完成行程。"
            lines = []
            for item in sorted(completed_items, key=lambda x: x.start_time):
                when = item.start_time.strftime("%Y-%m-%d %H:%M")
                lines.append(f"- [{item.schedule_id[:8]}] {when} {item.title}（已完成）")
            return "已完成行程：\n" + "\n".join(lines)

        if list_range == "all":
            visible_items = [item for item in items if item.status in {"scheduled", "completed"}]
            if not visible_items:
                return "目前沒有行程。"
            lines = []
            for item in sorted(visible_items, key=lambda x: x.start_time):
                when = item.start_time.strftime("%Y-%m-%d %H:%M")
                status_label = "已完成" if item.status == "completed" else "未完成"
                lines.append(f"- [{item.schedule_id[:8]}] {when} {item.title}（{status_label}）")
            return "全部行程：\n" + "\n".join(lines)

        if not items:
            return "無未完成行程，可查詢已完成行程。"
        lines = []
        for item in sorted(items, key=lambda x: x.start_time):
            if item.status != "scheduled":
                continue
            when = item.start_time.strftime("%Y-%m-%d %H:%M")
            lines.append(f"- [{item.schedule_id[:8]}] {when} {item.title}")
        if not lines:
            return "無未完成行程，可查詢已完成行程。"
        return "你的行程：\n" + "\n".join(lines)

    @staticmethod
    def _format_created(item: ScheduleItem) -> str:
        when = item.start_time.strftime("%Y-%m-%d %H:%M")
        return f"已新增行程：{when} {item.title}（ID:{item.schedule_id[:8]}）"

    @staticmethod
    def _format_updated(item: ScheduleItem | None) -> str:
        if not item:
            return "找不到要更新的行程。"
        when = item.start_time.strftime("%Y-%m-%d %H:%M")
        return f"已更新行程：{when} {item.title}（ID:{item.schedule_id[:8]}）"

    @staticmethod
    def _format_deleted(item: ScheduleItem | None) -> str:
        if not item:
            return "找不到要刪除的行程。"
        return f"已取消行程（ID:{item.schedule_id[:8]}）"

    @staticmethod
    def _format_completed(item: ScheduleItem | None) -> str:
        if not item:
            return "找不到要完成的行程。"
        when = item.start_time.strftime("%Y-%m-%d %H:%M")
        return f"已完成行程：{when} {item.title}（ID:{item.schedule_id[:8]}）"

    def _resolve_schedule(self, user_id: str, schedule_id: str) -> tuple[ScheduleItem | None, str | None]:
        items = self.schedule_store.list(user_id)
        matches = [item for item in items if item.schedule_id.startswith(schedule_id)]
        if not matches:
            return None, "找不到要刪除的行程。"
        if len(matches) > 1:
            return None, "找到多筆行程符合此 ID，請提供完整 ID。"
        return matches[0], None
