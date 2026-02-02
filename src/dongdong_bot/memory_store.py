from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List
from datetime import datetime, timedelta


@dataclass
class MemoryEntry:
    date: str
    content: str


class MemoryStore:
    def __init__(self, base_dir: str) -> None:
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _file_path(self, date: str) -> Path:
        return self.base_dir / f"{date}.md"

    def save(self, content: str, date: str | None = None) -> Path:
        date = date or datetime.now().strftime("%Y-%m-%d")
        path = self._file_path(date)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(f"- {content.strip()}\n")
        return path

    def query(self, query: str, date: str | None = None) -> List[str]:
        date = date or datetime.now().strftime("%Y-%m-%d")
        path = self._file_path(date)
        if not path.exists():
            return []
        results = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if query in line:
                results.append(line.lstrip("- "))
        return results

    def query_range(self, query: str, start: str, end: str) -> List[str]:
        results: List[str] = []
        for date in self._date_range(start, end):
            results.extend(self.query(query, date=date))
        return results

    def _date_range(self, start: str, end: str) -> Iterable[str]:
        start_dt = self._parse_date(start)
        end_dt = self._parse_date(end)
        current = start_dt
        step = 1 if end_dt >= start_dt else -1
        while True:
            yield current.strftime("%Y-%m-%d")
            if current == end_dt:
                break
            current = current + timedelta(days=step)

    def _parse_date(self, date_str: str) -> datetime:
        return datetime.strptime(date_str, "%Y-%m-%d")
