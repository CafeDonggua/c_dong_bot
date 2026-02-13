from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import re


WEEKDAY_MAP = {
    "日": 0,
    "天": 0,
    "一": 1,
    "二": 2,
    "三": 3,
    "四": 4,
    "五": 5,
    "六": 6,
}


@dataclass(frozen=True)
class CronNLParseResult:
    intent_kind: str
    schedule_kind: str | None = None
    schedule_value: str | None = None
    title: str = ""
    message: str = ""
    reason: str = ""
    clarification_hint: str = ""

    @property
    def valid(self) -> bool:
        return (
            self.intent_kind == "repeating"
            and bool(self.schedule_kind)
            and bool(self.schedule_value)
            and bool(self.title)
        )


class CronNaturalLanguageParser:
    _single_date_pattern = re.compile(r"\d{4}-\d{2}-\d{2}")
    _digital_time_pattern = re.compile(r"(?:早上|上午|下午|晚上|傍晚)?\s*\d{1,2}:\d{2}")
    _point_time_pattern = re.compile(
        r"(?:早上|上午|下午|晚上|傍晚)?\s*(?:\d{1,2}|[一二三四五六七八九十兩]{1,2})\s*點(?:半)?"
    )

    def parse(self, text: str, now: datetime | None = None) -> CronNLParseResult | None:
        _ = now  # 保留參數以利後續擴充相對時間解析
        cleaned = self._clean_text(text)
        if not cleaned or cleaned.startswith("/"):
            return None

        has_repeat = self._has_repeat_marker(cleaned)
        has_single = self._has_single_marker(cleaned)

        if has_repeat and has_single:
            return CronNLParseResult(
                intent_kind="unknown",
                reason="mixed_repeat_single",
                clarification_hint=(
                    "你的描述同時有單次與重複語意，請擇一：\n"
                    "- 單次：明天 14:00 開會\n"
                    "- 重複：每天 14:00 提醒我開會"
                ),
            )

        if has_repeat:
            return self._parse_repeating(cleaned)

        if has_single and self._has_time_hint(cleaned):
            return CronNLParseResult(
                intent_kind="single_event",
                reason="single_event_detected",
            )

        return None

    def _parse_repeating(self, text: str) -> CronNLParseResult:
        interval = self._parse_interval(text)
        if interval is not None:
            title = self._extract_title(text)
            if not title:
                return self._missing_title()
            return CronNLParseResult(
                intent_kind="repeating",
                schedule_kind="every",
                schedule_value=str(interval),
                title=title,
                message=title,
                reason="interval_detected",
            )

        if "每天" in text or "每日" in text:
            parsed_time = self._parse_time(text)
            if parsed_time is None:
                return self._missing_time()
            title = self._extract_title(text)
            if not title:
                return self._missing_title()
            hour, minute = parsed_time
            return CronNLParseResult(
                intent_kind="repeating",
                schedule_kind="cron",
                schedule_value=f"{minute} {hour} * * *",
                title=title,
                message=title,
                reason="daily_detected",
            )

        weekly_match = re.search(r"每(?:週|周)\s*([一二三四五六日天])", text)
        if weekly_match:
            parsed_time = self._parse_time(text)
            if parsed_time is None:
                return self._missing_time()
            title = self._extract_title(text)
            if not title:
                return self._missing_title()
            hour, minute = parsed_time
            weekday = WEEKDAY_MAP[weekly_match.group(1)]
            return CronNLParseResult(
                intent_kind="repeating",
                schedule_kind="cron",
                schedule_value=f"{minute} {hour} * * {weekday}",
                title=title,
                message=title,
                reason="weekly_detected",
            )

        return CronNLParseResult(
            intent_kind="unknown",
            reason="unsupported_repeat_pattern",
            clarification_hint=(
                "目前可用格式例如：\n"
                "- 每天 9 點提醒我喝水\n"
                "- 每 30 分鐘提醒站起來\n"
                "- 每週一 18:20 提醒我交週報"
            ),
        )

    @staticmethod
    def _parse_interval(text: str) -> int | None:
        match = re.search(
            r"每(?:隔)?\s*(\d+)\s*(秒|秒鐘|分|分鐘|小時|鐘頭)",
            text,
        )
        if not match:
            return None
        amount = int(match.group(1))
        unit = match.group(2)
        if amount <= 0:
            return None
        if unit in {"秒", "秒鐘"}:
            return amount
        if unit in {"分", "分鐘"}:
            return amount * 60
        return amount * 60 * 60

    def _parse_time(self, text: str) -> tuple[int, int] | None:
        digital = re.search(r"(早上|上午|下午|晚上|傍晚)?\s*(\d{1,2}):(\d{2})", text)
        if digital:
            period = digital.group(1) or ""
            hour = int(digital.group(2))
            minute = int(digital.group(3))
            return self._normalize_hour(period, hour), minute

        point = re.search(
            r"(早上|上午|下午|晚上|傍晚)?\s*(\d{1,2}|[一二三四五六七八九十兩]{1,2})\s*點(半)?",
            text,
        )
        if not point:
            return None
        period = point.group(1) or ""
        raw_hour = point.group(2)
        half = point.group(3)
        if re.fullmatch(r"\d{1,2}", raw_hour):
            hour = int(raw_hour)
        else:
            hour = self._parse_chinese_hour(raw_hour)
            if hour is None:
                return None
        minute = 30 if half else 0
        return self._normalize_hour(period, hour), minute

    @staticmethod
    def _normalize_hour(period: str, hour: int) -> int:
        if period in {"下午", "晚上", "傍晚"} and hour < 12:
            return hour + 12
        if period in {"早上", "上午"} and hour == 12:
            return 0
        return hour

    @staticmethod
    def _parse_chinese_hour(value: str) -> int | None:
        mapping = {
            "零": 0,
            "一": 1,
            "二": 2,
            "兩": 2,
            "三": 3,
            "四": 4,
            "五": 5,
            "六": 6,
            "七": 7,
            "八": 8,
            "九": 9,
            "十": 10,
        }
        if value in mapping:
            return mapping[value]
        if value.startswith("十") and len(value) == 2:
            tail = mapping.get(value[1])
            return 10 + tail if tail is not None else None
        if value.endswith("十") and len(value) == 2:
            head = mapping.get(value[0])
            return head * 10 if head is not None else None
        if len(value) == 2:
            head = mapping.get(value[0])
            tail = mapping.get(value[1])
            if head is None or tail is None:
                return None
            return head * 10 + tail
        return None

    @staticmethod
    def _extract_title(text: str) -> str:
        match = re.search(r"(?:提醒我|提醒)\s*(.+)$", text)
        if not match:
            return ""
        candidate = match.group(1).strip().strip("。！？!?,，")
        return candidate

    def _has_repeat_marker(self, text: str) -> bool:
        if "提醒" not in text:
            return False
        if "每天" in text or "每日" in text or "每週" in text or "每周" in text:
            return True
        return bool(re.search(r"每(?:隔)?\s*\d+\s*(?:秒|秒鐘|分|分鐘|小時|鐘頭)", text))

    def _has_single_marker(self, text: str) -> bool:
        if any(token in text for token in ("今天", "明天", "後天")):
            return True
        return bool(self._single_date_pattern.search(text))

    def _has_time_hint(self, text: str) -> bool:
        return bool(
            self._digital_time_pattern.search(text) or self._point_time_pattern.search(text)
        )

    @staticmethod
    def _clean_text(text: str) -> str:
        return " ".join(text.strip().split())

    @staticmethod
    def _missing_time() -> CronNLParseResult:
        return CronNLParseResult(
            intent_kind="unknown",
            reason="missing_time",
            clarification_hint=(
                "請補上提醒時間，例如：\n"
                "- 每天 9 點提醒我喝水\n"
                "- 每週一 18:20 提醒我交週報"
            ),
        )

    @staticmethod
    def _missing_title() -> CronNLParseResult:
        return CronNLParseResult(
            intent_kind="unknown",
            reason="missing_title",
            clarification_hint=(
                "請補上提醒內容，例如：\n"
                "- 每 30 分鐘提醒站起來\n"
                "- 每天 9 點提醒我喝水"
            ),
        )
