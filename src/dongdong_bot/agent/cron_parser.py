from __future__ import annotations

from dataclasses import dataclass, field
import re

from dongdong_bot.cron.schedule_rules import normalize_schedule


ALLOWED_LIST_STATUSES = {"scheduled", "paused", "completed", "failed"}
TASK_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{4,64}$")


@dataclass
class CronCommand:
    action: str
    task_id: str | None = None
    name: str = ""
    message: str = ""
    schedule_kind: str | None = None
    schedule_value: str | None = None
    status_filter: str | None = None
    enabled: bool | None = None
    errors: list[str] = field(default_factory=list)

    @property
    def valid(self) -> bool:
        return not self.errors


class CronParser:
    def parse(self, text: str) -> CronCommand | None:
        cleaned = text.strip()
        if cleaned != "/cron" and not cleaned.startswith("/cron "):
            return None

        body = cleaned[5:].strip()
        if not body:
            return CronCommand(action="help")

        args = body.split()
        action = args[0].lower()
        tail = body[len(args[0]) :].strip()

        if action in {"help", "h"}:
            return CronCommand(action="help")
        if action in {"list", "ls"}:
            return self._parse_list(tail)
        if action in {"remove", "delete", "rm"}:
            return self._parse_task_action("remove", tail)
        if action == "enable":
            return self._parse_task_action("enable", tail)
        if action == "disable":
            return self._parse_task_action("disable", tail)
        if action == "add":
            return self._parse_add(tail)

        return CronCommand(action="invalid", errors=[f"不支援的 /cron 子命令: {action}"])

    def _parse_list(self, tail: str) -> CronCommand:
        status = tail.strip().lower()
        if not status:
            return CronCommand(action="list")
        if status not in ALLOWED_LIST_STATUSES:
            return CronCommand(
                action="list",
                errors=[f"不支援的狀態篩選: {status}"],
            )
        return CronCommand(action="list", status_filter=status)

    def _parse_task_action(self, action: str, tail: str) -> CronCommand:
        task_id = tail.strip().split(" ", 1)[0] if tail.strip() else ""
        if not task_id:
            return CronCommand(action=action, errors=["缺少 task_id。"])
        if not TASK_ID_PATTERN.fullmatch(task_id):
            return CronCommand(action=action, errors=["task_id 格式不正確。"])
        enabled = None
        if action == "enable":
            enabled = True
        elif action == "disable":
            enabled = False
        return CronCommand(action=action, task_id=task_id, enabled=enabled)

    def _parse_add(self, tail: str) -> CronCommand:
        body = tail.strip()
        if not body:
            return CronCommand(action="add", errors=["缺少排程型態或排程值。"])
        kind_and_rest = body.split(None, 1)
        if len(kind_and_rest) < 2:
            return CronCommand(action="add", errors=["缺少排程型態或排程值。"])
        raw_kind = kind_and_rest[0]
        raw_value, payload = self._extract_schedule_value(raw_kind, kind_and_rest[1])
        if not raw_value:
            return CronCommand(action="add", errors=["缺少排程值。"])

        try:
            schedule_kind, schedule_value = normalize_schedule(raw_kind, raw_value)
        except ValueError as exc:
            return CronCommand(action="add", errors=[str(exc)])

        name, message = self._split_name_and_message(payload)
        if not name:
            return CronCommand(action="add", errors=["缺少任務名稱。"])
        return CronCommand(
            action="add",
            name=name,
            message=message or name,
            schedule_kind=schedule_kind,
            schedule_value=schedule_value,
        )

    @staticmethod
    def _split_name_and_message(payload: str) -> tuple[str, str]:
        raw = payload.strip()
        if not raw:
            return "", ""
        if "|" in raw:
            name, message = raw.split("|", 1)
            return name.strip(), message.strip()
        return raw, raw

    @staticmethod
    def _extract_schedule_value(kind: str, rest: str) -> tuple[str, str]:
        raw_rest = rest.strip()
        if not raw_rest:
            return "", ""
        lowered_kind = kind.strip().lower()
        if lowered_kind == "at":
            chunks = raw_rest.split(None, 2)
            if (
                len(chunks) >= 2
                and re.fullmatch(r"\d{4}-\d{2}-\d{2}", chunks[0])
                and re.fullmatch(r"\d{1,2}:\d{2}", chunks[1])
            ):
                value = f"{chunks[0]}T{chunks[1]}"
                payload = chunks[2] if len(chunks) > 2 else ""
                return value, payload.strip()
            chunks = raw_rest.split(None, 1)
            value = chunks[0]
            payload = chunks[1] if len(chunks) > 1 else ""
            return value.strip(), payload.strip()

        if lowered_kind != "cron":
            chunks = raw_rest.split(None, 1)
            value = chunks[0]
            payload = chunks[1] if len(chunks) > 1 else ""
            return value.strip(), payload.strip()

        if raw_rest[0] in {"'", '"'}:
            quote = raw_rest[0]
            end = raw_rest.find(quote, 1)
            if end == -1:
                return "", ""
            value = raw_rest[1:end].strip()
            payload = raw_rest[end + 1 :].strip()
            return value, payload

        chunks = raw_rest.split()
        if len(chunks) < 5:
            return raw_rest, ""
        value = " ".join(chunks[:5]).strip()
        payload = " ".join(chunks[5:]).strip()
        return value, payload
