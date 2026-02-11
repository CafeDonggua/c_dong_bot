from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List

from dongdong_bot.agent.cron_parser import CronCommand
from dongdong_bot.agent.cron_models import CronTask
from dongdong_bot.agent.cron_store import CronStore
from dongdong_bot.cron.schedule_rules import next_run_at


@dataclass
class CronResult:
    reply: str


class CronService:
    def __init__(self, cron_store: CronStore) -> None:
        self.cron_store = cron_store

    def handle(
        self,
        command: CronCommand,
        user_id: str,
        chat_id: str,
        now: datetime | None = None,
    ) -> CronResult:
        if command.errors:
            return CronResult(reply=self._format_parse_error(command))
        if command.action == "help":
            return CronResult(reply=self._help_text())
        if command.action == "add":
            if not command.schedule_kind or not command.schedule_value:
                return CronResult(
                    reply=(
                        "缺少排程資訊，請使用 /cron add <at|every|cron> ...\n"
                        "例如：/cron add every 60 喝水提醒 | 請喝水"
                    )
                )
            current = now or datetime.now()
            try:
                next_time = next_run_at(
                    command.schedule_kind,
                    command.schedule_value,
                    reference_time=current,
                )
            except ValueError as exc:
                return CronResult(reply=str(exc))
            if next_time is None:
                return CronResult(reply="排程時間已過，請重新設定。")
            task = self.cron_store.create(
                owner_user_id=user_id,
                owner_chat_id=chat_id,
                name=command.name.strip(),
                message=command.message.strip() or command.name.strip(),
                schedule_kind=command.schedule_kind,
                schedule_value=command.schedule_value,
                next_run_at=next_time,
            )
            return CronResult(reply=self._format_created(task.task_id, task.name, next_time))
        if command.action == "list":
            tasks = self.cron_store.list(
                owner_user_id=user_id,
                status=command.status_filter,
            )
            return CronResult(reply=self._format_list(tasks, command.status_filter))
        if command.action == "remove":
            if not command.task_id:
                return CronResult(reply="請提供 task_id，例如：/cron remove abcd1234")
            removed, error = self.cron_store.remove_for_owner(user_id, command.task_id)
            if error:
                return CronResult(reply=error)
            if not removed:
                return CronResult(reply="刪除失敗，請稍後再試。")
            return CronResult(reply=f"已刪除 /cron 任務（ID:{command.task_id}）。")
        if command.action in {"enable", "disable"}:
            if not command.task_id:
                return CronResult(
                    reply=f"請提供 task_id，例如：/cron {command.action} abcd1234"
                )
            task, error = self.cron_store.resolve_for_owner(user_id, command.task_id)
            if error:
                return CronResult(reply=error)
            if task is None:
                return CronResult(reply="找不到任務。")
            if command.action == "disable":
                if not task.enabled and task.status == "paused":
                    return CronResult(reply=f"任務已停用（ID:{task.task_id[:8]}）。")
                updated, update_error = self.cron_store.mark_disabled_for_owner(
                    user_id,
                    command.task_id,
                    enabled=False,
                )
                if update_error:
                    return CronResult(reply=update_error)
                if not updated:
                    return CronResult(reply="停用失敗，請稍後再試。")
                return CronResult(reply=f"已停用任務（ID:{updated.task_id[:8]}）。")

            if task.status == "completed":
                return CronResult(reply="任務已完成，無法重新啟用。")
            current = now or datetime.now()
            next_time = task.next_run_at
            if next_time is None or next_time <= current:
                try:
                    next_time = next_run_at(
                        task.schedule_kind,
                        task.schedule_value,
                        reference_time=current,
                        last_run_at=task.last_run_at,
                    )
                except ValueError as exc:
                    return CronResult(reply=str(exc))
                if next_time is None:
                    return CronResult(reply="任務已無可用的下次觸發時間，請重新建立任務。")
            updated = self.cron_store.update(
                task.task_id,
                enabled=True,
                status="scheduled",
                next_run_at=next_time,
            )
            if not updated:
                return CronResult(reply="啟用失敗，請稍後再試。")
            when = next_time.strftime("%Y-%m-%d %H:%M")
            return CronResult(reply=f"已啟用任務（ID:{updated.task_id[:8]}，下次觸發：{when}）。")
        return CronResult(reply=self._help_text())

    @staticmethod
    def _format_parse_error(command: CronCommand) -> str:
        error = command.errors[0]
        if command.action == "add":
            if "every 排程需提供正整數秒數" in error:
                return f"{error}\n例如：/cron add every 300 每5分鐘提醒 | 起來走走"
            if "at 排程需提供合法時間" in error:
                return f"{error}\n例如：/cron add at 2026-02-11T23:50 單次提醒 | 23:50 開會"
            if "cron 排程格式不合法" in error:
                return (
                    f"{error}\n"
                    "例如：/cron add cron \"*/30 * * * *\" 半小時提醒 | 起來動一動"
                )
            return f"{error}\n例如：/cron add every 60 喝水提醒 | 請喝水"
        if command.action == "list":
            return f"{error}\n例如：/cron list scheduled"
        if command.action in {"remove", "enable", "disable"}:
            return f"{error}\n例如：/cron {command.action} abcd1234"
        if command.action == "invalid":
            return f"{error}\n例如：/cron help"
        return f"{error}\n可先用 /cron help 查看完整用法。"

    @staticmethod
    def _help_text() -> str:
        return (
            "用法：\n"
            "/cron add at <YYYY-MM-DDTHH:MM> <任務名稱> | <提醒訊息>\n"
            "/cron add every <秒數> <任務名稱> | <提醒訊息>\n"
            "/cron add cron \"<分 時 日 月 週>\" <任務名稱> | <提醒訊息>\n"
            "/cron list [scheduled|paused|completed|failed]\n"
            "/cron remove <task_id>\n"
            "/cron enable <task_id>\n"
            "/cron disable <task_id>"
        )

    @staticmethod
    def _format_created(task_id: str, name: str, next_time: datetime) -> str:
        when = next_time.strftime("%Y-%m-%d %H:%M")
        short_id = task_id[:8]
        return f"已建立 /cron 任務：{name}（ID:{short_id}，下次觸發：{when}）"

    @staticmethod
    def _format_list(tasks: List[CronTask], status_filter: str | None) -> str:
        if not tasks:
            if status_filter:
                return f"目前沒有狀態為 {status_filter} 的 /cron 任務。"
            return "目前沒有 /cron 任務。"
        lines: List[str] = []
        sorted_tasks = sorted(
            tasks,
            key=lambda item: (item.next_run_at is None, item.next_run_at or datetime.max),
        )
        for task in sorted_tasks:
            next_run = task.next_run_at.strftime("%Y-%m-%d %H:%M") if task.next_run_at else "-"
            lines.append(
                f"- [{task.task_id[:8]}] {task.name} | {task.schedule_kind}:{task.schedule_value} | "
                f"狀態:{task.status} | 啟用:{'是' if task.enabled else '否'} | 下次:{next_run}"
            )
        return "/cron 任務清單：\n" + "\n".join(lines)
