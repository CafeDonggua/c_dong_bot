from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List
import json


@dataclass(frozen=True)
class AllowlistEntry:
    user_id: str
    channel_type: str


class AllowlistStore:
    def __init__(self, path: str) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def is_allowed(self, user_id: str, channel_type: str) -> bool:
        entries = self.list_entries()
        if not entries:
            return True
        return any(
            entry.user_id == user_id and entry.channel_type == channel_type
            for entry in entries
        )

    def list_entries(self) -> List[AllowlistEntry]:
        data = self._load()
        return [AllowlistEntry(**item) for item in data]

    def add(self, entry: AllowlistEntry) -> None:
        data = self._load()
        if any(
            item.get("user_id") == entry.user_id
            and item.get("channel_type") == entry.channel_type
            for item in data
        ):
            return
        data.append({"user_id": entry.user_id, "channel_type": entry.channel_type})
        self._write(data)

    def remove(self, user_id: str, channel_type: str) -> None:
        data = self._load()
        filtered = [
            item
            for item in data
            if not (
                item.get("user_id") == user_id
                and item.get("channel_type") == channel_type
            )
        ]
        self._write(filtered)

    def seed(self, entries: Iterable[AllowlistEntry]) -> None:
        data = [
            {"user_id": entry.user_id, "channel_type": entry.channel_type}
            for entry in entries
        ]
        self._write(data)

    def _load(self) -> List[dict]:
        if not self.path.exists():
            return []
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return []
        if not isinstance(data, list):
            return []
        cleaned = []
        for item in data:
            if not isinstance(item, dict):
                continue
            user_id = str(item.get("user_id", "")).strip()
            channel_type = str(item.get("channel_type", "")).strip()
            if user_id and channel_type:
                cleaned.append({"user_id": user_id, "channel_type": channel_type})
        return cleaned

    def _write(self, data: List[dict]) -> None:
        tmp_path = self.path.with_suffix(".tmp")
        tmp_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp_path.replace(self.path)
