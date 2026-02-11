from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta


SCHEDULE_KINDS = {"at", "every", "cron"}


def normalize_schedule(kind: str, value: str) -> tuple[str, str]:
    schedule_kind = kind.strip().lower()
    if schedule_kind not in SCHEDULE_KINDS:
        raise ValueError("不支援的排程型態，請使用 at、every 或 cron。")
    schedule_value = str(value).strip()
    if not schedule_value:
        raise ValueError("缺少排程值。")
    if schedule_kind == "at":
        at_time = _parse_iso_datetime(schedule_value)
        if at_time is None:
            raise ValueError("at 排程需提供合法時間，格式如 2026-02-11T09:00。")
        return schedule_kind, at_time.isoformat()
    if schedule_kind == "every":
        try:
            seconds = int(schedule_value)
        except ValueError as exc:
            raise ValueError("every 排程需提供正整數秒數。") from exc
        if seconds <= 0:
            raise ValueError("every 排程需提供正整數秒數。")
        return schedule_kind, str(seconds)
    if not is_valid_cron_expression(schedule_value):
        raise ValueError("cron 排程格式不合法，需為 5 欄位。")
    return schedule_kind, " ".join(schedule_value.split())


def next_run_at(
    kind: str,
    value: str,
    *,
    reference_time: datetime | None = None,
    last_run_at: datetime | None = None,
) -> datetime | None:
    schedule_kind, schedule_value = normalize_schedule(kind, value)
    reference = reference_time or datetime.now()
    if schedule_kind == "at":
        at_time = _parse_iso_datetime(schedule_value)
        if at_time is None or at_time <= reference:
            return None
        return at_time
    if schedule_kind == "every":
        seconds = int(schedule_value)
        candidate = (last_run_at or reference) + timedelta(seconds=seconds)
        while candidate <= reference:
            candidate += timedelta(seconds=seconds)
        return candidate
    return _next_from_cron(schedule_value, reference)


def is_valid_cron_expression(expression: str) -> bool:
    parts = expression.split()
    if len(parts) != 5:
        return False
    try:
        _parse_cron_fields(expression)
    except ValueError:
        return False
    return True


def _parse_iso_datetime(value: str) -> datetime | None:
    normalized = value.strip().replace(" ", "T")
    try:
        return datetime.fromisoformat(normalized)
    except ValueError:
        return None


@dataclass(frozen=True)
class _CronFields:
    minutes: set[int]
    hours: set[int]
    days_of_month: set[int]
    months: set[int]
    days_of_week: set[int]
    dom_any: bool
    dow_any: bool


def _parse_cron_fields(expression: str) -> _CronFields:
    minute, hour, day_of_month, month, day_of_week = expression.split()
    dow_values = _parse_field(day_of_week, 0, 7)
    normalized_dow = {0 if value == 7 else value for value in dow_values}
    return _CronFields(
        minutes=_parse_field(minute, 0, 59),
        hours=_parse_field(hour, 0, 23),
        days_of_month=_parse_field(day_of_month, 1, 31),
        months=_parse_field(month, 1, 12),
        days_of_week=normalized_dow,
        dom_any=day_of_month == "*",
        dow_any=day_of_week == "*",
    )


def _parse_field(raw: str, minimum: int, maximum: int) -> set[int]:
    values: set[int] = set()
    for chunk in raw.split(","):
        chunk = chunk.strip()
        if not chunk:
            raise ValueError("cron 欄位不可為空。")
        base, step = _split_step(chunk)
        if base == "*":
            start, end = minimum, maximum
        elif "-" in base:
            start_text, end_text = base.split("-", 1)
            start, end = int(start_text), int(end_text)
        else:
            start = end = int(base)
        if start < minimum or end > maximum or start > end:
            raise ValueError("cron 欄位超出允許範圍。")
        for value in range(start, end + 1, step):
            values.add(value)
    return values


def _split_step(chunk: str) -> tuple[str, int]:
    if "/" not in chunk:
        return chunk, 1
    base, step_text = chunk.split("/", 1)
    step = int(step_text)
    if step <= 0:
        raise ValueError("cron step 需為正整數。")
    return base, step


def _next_from_cron(expression: str, reference: datetime) -> datetime | None:
    fields = _parse_cron_fields(expression)
    candidate = reference.replace(second=0, microsecond=0) + timedelta(minutes=1)
    deadline = reference + timedelta(days=366)
    while candidate <= deadline:
        if _cron_match(candidate, fields):
            return candidate
        candidate += timedelta(minutes=1)
    return None


def _cron_match(candidate: datetime, fields: _CronFields) -> bool:
    if candidate.minute not in fields.minutes:
        return False
    if candidate.hour not in fields.hours:
        return False
    if candidate.month not in fields.months:
        return False
    dom_match = candidate.day in fields.days_of_month
    dow_value = (candidate.weekday() + 1) % 7
    dow_match = dow_value in fields.days_of_week
    if fields.dom_any and fields.dow_any:
        day_match = True
    elif fields.dom_any:
        day_match = dow_match
    elif fields.dow_any:
        day_match = dom_match
    else:
        day_match = dom_match or dow_match
    return day_match
