from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
import re
from typing import Optional


@dataclass
class ScheduleCommand:
    action: str
    title: str
    start_time: Optional[datetime] = None
    schedule_id: Optional[str] = None


class ScheduleParser:
    def parse(self, text: str, now: Optional[datetime] = None) -> Optional[ScheduleCommand]:
        cleaned = text.strip()
        if not cleaned:
            return None
        now = now or datetime.now()
        if self._is_list(cleaned):
            return ScheduleCommand(action="list", title="")
        delete_id = self._extract_id(cleaned)
        if self._is_delete(cleaned) and delete_id:
            return ScheduleCommand(action="delete", title="", schedule_id=delete_id)
        update_id = self._extract_id(cleaned)
        if self._is_update(cleaned) and update_id:
            start_time = self._extract_datetime(cleaned, now)
            title = self._extract_title(cleaned)
            if title == "行程":
                title = ""
            return ScheduleCommand(
                action="update",
                title=title,
                start_time=start_time,
                schedule_id=update_id,
            )
        if self._is_add(cleaned):
            start_time = self._extract_datetime(cleaned, now)
            title = self._extract_title(cleaned)
            if start_time:
                return ScheduleCommand(action="add", title=title, start_time=start_time)
        return None

    @staticmethod
    def _is_list(text: str) -> bool:
        keywords = ("有哪些行程", "行程列表", "行程清單", "我有哪些行程", "行程有哪些")
        return any(keyword in text for keyword in keywords)

    @staticmethod
    def _is_delete(text: str) -> bool:
        return text.startswith("刪除") or text.startswith("取消") or text.startswith("刪掉")

    @staticmethod
    def _is_update(text: str) -> bool:
        return text.startswith("修改") or text.startswith("更改") or "改成" in text

    @staticmethod
    def _is_add(text: str) -> bool:
        keywords = ("記錄", "新增行程", "安排", "提醒")
        return any(keyword in text for keyword in keywords)

    @staticmethod
    def _extract_id(text: str) -> Optional[str]:
        match = re.search(r"[0-9a-f]{8,}", text)
        if not match:
            return None
        return match.group(0)

    def _extract_datetime(self, text: str, now: datetime) -> Optional[datetime]:
        date_part = None
        match = re.search(r"(\d{4}-\d{2}-\d{2})", text)
        if match:
            date_part = match.group(1)
        elif "今天" in text:
            date_part = now.strftime("%Y-%m-%d")
        elif "明天" in text:
            date_part = (now + timedelta(days=1)).strftime("%Y-%m-%d")
        elif "後天" in text:
            date_part = (now + timedelta(days=2)).strftime("%Y-%m-%d")
        time_match = re.search(r"(\d{1,2}):(\d{2})", text)
        if not time_match:
            return None
        hour = int(time_match.group(1))
        minute = int(time_match.group(2))
        if date_part is None:
            date_part = now.strftime("%Y-%m-%d")
        try:
            return datetime.strptime(f"{date_part} {hour:02d}:{minute:02d}", "%Y-%m-%d %H:%M")
        except ValueError:
            return None

    @staticmethod
    def _extract_title(text: str) -> str:
        stripped = re.sub(r"\d{4}-\d{2}-\d{2}", "", text)
        stripped = re.sub(r"\d{1,2}:\d{2}", "", stripped)
        for keyword in ("幫我", "請", "記錄", "新增行程", "安排", "提醒", "修改", "更改", "改成", "刪除", "取消", "刪掉"):
            stripped = stripped.replace(keyword, "")
        stripped = stripped.replace("今天", "").replace("明天", "").replace("後天", "")
        stripped = stripped.strip(" ：:，,。.!？?　")
        return stripped or "行程"
