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
    end_time: Optional[datetime] = None
    description: str = ""
    schedule_id: Optional[str] = None
    list_range: str = "default"
    intent: str = "clear"
    message: str = ""


class ScheduleParser:
    def parse(self, text: str, now: Optional[datetime] = None) -> Optional[ScheduleCommand]:
        cleaned = text.strip()
        if not cleaned:
            return None
        now = now or datetime.now()
        if self._is_list(cleaned):
            if self._is_completed_list(cleaned):
                list_range = "completed"
            elif self._is_all_list(cleaned):
                list_range = "all"
            else:
                list_range = "default"
            return ScheduleCommand(action="list", title="", list_range=list_range)
        reply_token = cleaned.strip(" 　。.!！？?，,、")
        if self._is_confirm_reply(reply_token):
            return ScheduleCommand(action="bulk_delete_confirm", title="", intent="confirm")
        if self._is_cancel_reply(reply_token):
            return ScheduleCommand(action="bulk_delete_cancel", title="", intent="cancel")
        if self._is_bulk_delete_completed(cleaned):
            return ScheduleCommand(action="bulk_delete_completed", title="")
        delete_intent = self._has_delete_intent(cleaned)
        complete_intent = self._has_complete_intent(cleaned)
        if delete_intent or complete_intent:
            ids = self._extract_ids(cleaned)
            if len(ids) > 1:
                return ScheduleCommand(
                    action="clarify",
                    title="",
                    intent="invalid",
                    message="一次只能指定一個行程 ID，請重新輸入。",
                )
            schedule_id = ids[0] if ids else None
            if delete_intent and complete_intent:
                return ScheduleCommand(
                    action="clarify",
                    title="",
                    schedule_id=schedule_id,
                    intent="ambiguous",
                    message="請問要刪除還是標示完成？",
                )
            if delete_intent:
                return ScheduleCommand(
                    action="delete",
                    title="",
                    schedule_id=schedule_id,
                    intent="invalid" if not schedule_id else "delete",
                    message="請先提供行程 ID，可先查詢行程清單。" if not schedule_id else "",
                )
            return ScheduleCommand(
                action="complete",
                title="",
                schedule_id=schedule_id,
                intent="invalid" if not schedule_id else "complete",
                message="請先提供行程 ID，可先查詢行程清單。" if not schedule_id else "",
            )
        update_id = self._extract_id(cleaned)
        if self._is_update(cleaned):
            if not update_id:
                return ScheduleCommand(
                    action="clarify",
                    title="",
                    intent="invalid",
                    message="請先提供行程 ID，可先查詢行程清單。",
                )
            start_time = self._extract_datetime(cleaned, now)
            end_time = self._extract_end_datetime(cleaned, now)
            description = self._extract_description(cleaned)
            title = self._extract_title(cleaned)
            if title == "行程":
                title = ""
            return ScheduleCommand(
                action="update",
                title=title,
                description=description,
                start_time=start_time,
                end_time=end_time,
                schedule_id=update_id,
            )
        if self._is_add(cleaned):
            start_time = self._extract_datetime(cleaned, now)
            title = self._extract_title(cleaned)
            if start_time:
                return ScheduleCommand(action="add", title=title, start_time=start_time)
        return None

    @staticmethod
    def is_schedule_hint(text: str) -> bool:
        keywords = ("行程", "安排", "開會", "剪頭髮", "看醫生", "提醒", "約", "排程")
        return any(keyword in text for keyword in keywords)

    @staticmethod
    def has_date_hint(text: str) -> bool:
        return bool(
            re.search(r"(\d{4}-\d{2}-\d{2})", text)
            or any(keyword in text for keyword in ("今天", "明天", "後天", "週", "星期"))
        )

    @staticmethod
    def has_time_hint(text: str) -> bool:
        return bool(
            re.search(r"(\d{1,2}):(\d{2})", text)
            or re.search(r"(早上|上午|下午|晚上|傍晚)?\s*(\d{1,2})點(半)?", text)
        )

    def _is_list(self, text: str) -> bool:
        explicit = (
            "有哪些行程",
            "行程列表",
            "行程清單",
            "我有哪些行程",
            "行程有哪些",
            "我最近有什麼行程",
            "我最近有哪些行程",
            "最近有什麼行程",
            "最近有哪些行程",
            "我最近有什麼安排",
            "我最近有哪些安排",
            "最近有什麼安排",
            "最近有哪些安排",
            "我最近要做什麼",
            "已完成行程",
            "歷史行程",
            "全部行程",
            "所有行程",
        )
        if any(keyword in text for keyword in explicit):
            has_action_intent = self._has_delete_intent(text) or self._has_complete_intent(text)
            has_action_intent = has_action_intent or self._is_update(text) or self._is_add(text)
            if not has_action_intent:
                return True
            return False
        if "行程" not in text:
            return False
        list_verbs = ("列出", "查詢", "顯示", "看看", "有哪些", "清單", "列表")
        if any(keyword in text for keyword in list_verbs):
            return True
        list_modifiers = ("最近", "現在", "全部", "所有", "已完成", "歷史")
        has_action_intent = self._has_delete_intent(text) or self._has_complete_intent(text)
        has_action_intent = has_action_intent or self._is_update(text) or self._is_add(text)
        if any(keyword in text for keyword in list_modifiers) and not has_action_intent:
            return True
        return False

    @staticmethod
    def _is_completed_list(text: str) -> bool:
        keywords = ("已完成", "已經完成", "完成的行程", "已完成的行程", "歷史行程", "歷史")
        return any(keyword in text for keyword in keywords)

    @staticmethod
    def _is_all_list(text: str) -> bool:
        return "全部" in text or "所有" in text

    @staticmethod
    def _is_bulk_delete_completed(text: str) -> bool:
        delete_keywords = ("刪除", "刪掉", "刪除掉", "清除", "清空")
        completed_keywords = ("已完成", "已經完成", "完成的", "完成")
        bulk_keywords = ("全部", "所有", "全都")
        if not any(keyword in text for keyword in delete_keywords):
            return False
        if not any(keyword in text for keyword in completed_keywords):
            return False
        if "行程" not in text:
            return False
        if any(keyword in text for keyword in bulk_keywords):
            return True
        return "已完成行程" in text or "完成的行程" in text

    @staticmethod
    def _has_delete_intent(text: str) -> bool:
        keywords = ("刪除", "刪掉", "刪除掉", "取消")
        return any(keyword in text for keyword in keywords)

    @staticmethod
    def _has_complete_intent(text: str) -> bool:
        if any(keyword in text for keyword in ("完成這", "完成該", "完成此", "完成掉")):
            return True
        if "完成" in text and any(keyword in text for keyword in ("標記", "標示", "表示")):
            return True
        return False

    @staticmethod
    def _is_update(text: str) -> bool:
        return text.startswith("修改") or text.startswith("更改") or "改成" in text

    @staticmethod
    def _is_add(text: str) -> bool:
        keywords = ("記錄", "紀錄", "新增行程", "安排", "提醒")
        return any(keyword in text for keyword in keywords)

    @staticmethod
    def _extract_ids(text: str) -> list[str]:
        return re.findall(r"[0-9a-fA-F]{8,}", text)

    @staticmethod
    def _extract_id(text: str) -> Optional[str]:
        ids = ScheduleParser._extract_ids(text)
        return ids[0] if ids else None

    @staticmethod
    def _is_confirm_reply(text: str) -> bool:
        confirm_keywords = ("確認", "確定", "好", "好的", "可以")
        return text in confirm_keywords

    @staticmethod
    def _is_cancel_reply(text: str) -> bool:
        cancel_keywords = ("取消", "不用了", "不要了", "算了", "先不要")
        return text in cancel_keywords

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
        hour = None
        minute = None
        time_match = re.search(r"(\d{1,2}):(\d{2})", text)
        if time_match:
            hour = int(time_match.group(1))
            minute = int(time_match.group(2))
        else:
            period_match = re.search(r"(早上|上午|下午|晚上|傍晚)?\s*(\d{1,2})點(半)?", text)
            if period_match:
                period = period_match.group(1) or ""
                hour = int(period_match.group(2))
                minute = 30 if period_match.group(3) else 0
                if period in {"下午", "晚上", "傍晚"} and hour < 12:
                    hour += 12
                if period in {"早上", "上午"} and hour == 12:
                    hour = 0
            else:
                cn_match = re.search(
                    r"(早上|上午|下午|晚上|傍晚)?\s*([一二三四五六七八九十兩]{1,2})點(半)?",
                    text,
                )
                if cn_match:
                    period = cn_match.group(1) or ""
                    hour = self._parse_chinese_hour(cn_match.group(2))
                    minute = 30 if cn_match.group(3) else 0
                    if hour is not None:
                        if period in {"下午", "晚上", "傍晚"} and hour < 12:
                            hour += 12
                        if period in {"早上", "上午"} and hour == 12:
                            hour = 0
        if hour is None or minute is None:
            return None
        if date_part is None:
            date_part = now.strftime("%Y-%m-%d")
        try:
            return datetime.strptime(f"{date_part} {hour:02d}:{minute:02d}", "%Y-%m-%d %H:%M")
        except ValueError:
            return None

    @staticmethod
    def _parse_chinese_hour(value: str) -> Optional[int]:
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

    def _extract_end_datetime(self, text: str, now: datetime) -> Optional[datetime]:
        for marker in ("結束時間", "結束", "到"):
            if marker not in text:
                continue
            _, tail = text.split(marker, 1)
            candidate = tail.strip()
            if not candidate:
                continue
            parsed = self._extract_datetime(candidate, now)
            if parsed:
                return parsed
        return None

    @staticmethod
    def _extract_description(text: str) -> str:
        match = re.search(r"(?:描述|說明|備註)[:：]\\s*(.+)", text)
        if match:
            return match.group(1).strip()
        return ""

    @staticmethod
    def _extract_title(text: str) -> str:
        stripped = re.sub(r"\d{4}-\d{2}-\d{2}", "", text)
        stripped = re.sub(r"\d{1,2}:\d{2}", "", stripped)
        stripped = re.sub(r"[0-9a-fA-F]{8,}", "", stripped)
        stripped = re.sub(r"(?:描述|說明|備註)[:：].*", "", stripped)
        for keyword in (
            "幫我",
            "請",
            "記錄",
            "紀錄",
            "新增行程",
            "安排",
            "提醒",
            "修改",
            "更改",
            "改成",
            "刪除",
            "取消",
            "刪掉",
            "結束時間",
            "結束",
            "到",
        ):
            stripped = stripped.replace(keyword, "")
        stripped = (
            stripped.replace("今天", "")
            .replace("明天", "")
            .replace("後天", "")
            .replace("早上", "")
            .replace("上午", "")
            .replace("下午", "")
            .replace("晚上", "")
            .replace("傍晚", "")
        )
        stripped = stripped.strip(" ：:，,。.!？?　")
        return stripped or "行程"
