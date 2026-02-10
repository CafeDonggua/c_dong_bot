from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Sequence
from datetime import datetime, timedelta
import json
from uuid import uuid4

from dongdong_bot.lib.report_writer import ReportWriter
from dongdong_bot.lib.vector_math import cosine_similarity, top_k_scored


@dataclass
class MemoryEntry:
    date: str
    content: str


class MemoryStore:
    def __init__(
        self,
        base_dir: str,
        embedding_index_path: str | None = None,
        memory_subdir: str = "memory",
        reports_subdir: str = "reports",
    ) -> None:
        self.root_dir = Path(base_dir)
        self.memory_dir = self.root_dir / memory_subdir
        self.reports_dir = self.root_dir / reports_subdir
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        self._ensure_writable(self.memory_dir)
        self._ensure_writable(self.reports_dir)
        self.embedding_index_path = (
            Path(embedding_index_path) if embedding_index_path else self.root_dir / "embeddings.jsonl"
        )
        self.embedding_index_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_writable(self.embedding_index_path.parent)
        self._legacy_dir = self.root_dir

    @staticmethod
    def _ensure_writable(path: Path) -> None:
        try:
            probe = path / ".writecheck"
            with probe.open("a", encoding="utf-8") as handle:
                handle.write("")
            probe.unlink(missing_ok=True)
        except Exception as exc:
            raise RuntimeError(f"記憶目錄不可寫入: {path}") from exc

    def _file_path(self, date: str) -> Path:
        return self.memory_dir / f"{date}.md"

    def log_report(self, title: str, report_path: Path, date: str | None = None) -> Path:
        date = date or datetime.now().strftime("%Y-%m-%d")
        path = self._file_path(date)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(ReportWriter.format_log_entry(title, report_path, self.root_dir) + "\n")
        return path

    def save(self, content: str, date: str | None = None) -> Path:
        date = date or datetime.now().strftime("%Y-%m-%d")
        path = self._file_path(date)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(f"- {content.strip()}\n")
        return path

    def save_with_embedding(
        self,
        content: str,
        embedding: Sequence[float],
        date: str | None = None,
    ) -> Path:
        date = date or datetime.now().strftime("%Y-%m-%d")
        path = self.save(content, date=date)
        record = {
            "id": uuid4().hex,
            "date": date,
            "content": content.strip(),
            "vector": list(embedding),
            "created_at": datetime.now().isoformat(),
        }
        with self.embedding_index_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
        return path

    def delete_all(self) -> int:
        removed = 0
        for path in self.memory_dir.glob("*.md"):
            removed += self._count_entries(path)
            path.unlink(missing_ok=True)
        if self.embedding_index_path.exists():
            removed += self._count_embedding_entries(self.embedding_index_path)
            self.embedding_index_path.unlink(missing_ok=True)
        return removed

    def delete_by_date_range(self, start: str, end: str) -> int:
        removed = 0
        dates = set(self._date_range(start, end))
        for date in dates:
            path = self._file_path(date)
            if path.exists():
                removed += self._count_entries(path)
                path.unlink(missing_ok=True)
        removed += self._filter_embedding_index(
            lambda record: str(record.get("date")) not in dates
        )
        return removed

    def delete_by_keyword(self, keyword: str, start: str | None = None, end: str | None = None) -> int:
        keyword = keyword.strip()
        if not keyword:
            return 0
        removed = 0
        target_dates = None
        if start and end:
            target_dates = set(self._date_range(start, end))
        for path in self.memory_dir.glob("*.md"):
            date = path.stem
            if target_dates is not None and date not in target_dates:
                continue
            lines = path.read_text(encoding="utf-8").splitlines()
            kept = [line for line in lines if keyword not in line]
            removed += len(lines) - len(kept)
            if kept:
                path.write_text("\n".join(kept) + "\n", encoding="utf-8")
            else:
                path.unlink(missing_ok=True)
        removed += self._filter_embedding_index(
            lambda record: not self._should_remove_record(record, keyword, target_dates)
        )
        return removed

    def query(self, query: str, date: str | None = None) -> List[str]:
        date = date or datetime.now().strftime("%Y-%m-%d")
        path = self._file_path(date)
        legacy_path = self._legacy_dir / f"{date}.md"
        if not path.exists() and not legacy_path.exists():
            return []
        results = []
        if path.exists():
            for line in path.read_text(encoding="utf-8").splitlines():
                if query in line:
                    results.append(line.lstrip("- "))
        if legacy_path.exists():
            for line in legacy_path.read_text(encoding="utf-8").splitlines():
                if query in line:
                    results.append(line.lstrip("- "))
        return results

    def semantic_search(
        self,
        query_embedding: Sequence[float],
        top_k: int = 5,
        min_score: float = 0.2,
    ) -> List[tuple[str, float]]:
        if not self.embedding_index_path.exists():
            return []
        scored: List[tuple[str, float]] = []
        for line in self.embedding_index_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            vector = record.get("vector")
            content = record.get("content", "")
            if not vector or not content:
                continue
            if self._is_noise_content(content):
                continue
            score = cosine_similarity(query_embedding, vector)
            if score >= min_score:
                scored.append((content, score))
        return self._dedupe(top_k_scored(scored, top_k))

    @staticmethod
    def filter_by_score(
        results: List[tuple[str, float]],
        min_score: float = 0.3,
        relative_drop: float = 0.15,
    ) -> List[tuple[str, float]]:
        if not results:
            return []
        top_score = results[0][1]
        cutoff = max(min_score, top_score - relative_drop)
        return [(content, score) for content, score in results if score >= cutoff]

    def query_range(self, query: str, start: str, end: str) -> List[str]:
        results: List[str] = []
        for date in self._date_range(start, end):
            results.extend(self.query(query, date=date))
        return results

    def summarize_results(
        self,
        results: List[str],
        max_items: int = 5,
        max_chars: int = 120,
    ) -> List[str]:
        if not results:
            return []
        trimmed = []
        for item in results:
            text = item.strip()
            if len(text) > max_chars:
                text = text[: max_chars - 1].rstrip() + "…"
            trimmed.append(text)
        deduped = []
        seen = set()
        for item in trimmed:
            if item in seen:
                continue
            seen.add(item)
            deduped.append(item)
        return deduped[:max_items]

    def recent_entries(
        self,
        days: int = 7,
        max_entries: int = 200,
    ) -> List[str]:
        today = datetime.now()
        entries: List[str] = []
        for offset in range(days):
            date_str = (today - timedelta(days=offset)).strftime("%Y-%m-%d")
            path = self._file_path(date_str)
            legacy_path = self._legacy_dir / f"{date_str}.md"
            for candidate in (path, legacy_path):
                if not candidate.exists():
                    continue
                for line in candidate.read_text(encoding="utf-8").splitlines():
                    if not line.strip():
                        continue
                    entries.append(line.lstrip("- ").strip())
                    if len(entries) >= max_entries:
                        return entries
        return entries

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

    @staticmethod
    def _is_noise_content(content: str) -> bool:
        trimmed = content.strip()
        noise_phrases = {"了什麼", "的事情"}
        return trimmed in noise_phrases

    @staticmethod
    def _dedupe(items: List[tuple[str, float]]) -> List[tuple[str, float]]:
        seen = set()
        deduped: List[tuple[str, float]] = []
        for content, score in items:
            if content in seen:
                continue
            seen.add(content)
            deduped.append((content, score))
        return deduped

    @staticmethod
    def _count_entries(path: Path) -> int:
        try:
            return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())
        except FileNotFoundError:
            return 0

    @staticmethod
    def _count_embedding_entries(path: Path) -> int:
        try:
            return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())
        except FileNotFoundError:
            return 0

    def _filter_embedding_index(self, keep_fn) -> int:
        if not self.embedding_index_path.exists():
            return 0
        kept = []
        removed = 0
        for line in self.embedding_index_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                kept.append(line)
                continue
            if keep_fn(record):
                kept.append(json.dumps(record, ensure_ascii=False))
            else:
                removed += 1
        if removed:
            self.embedding_index_path.write_text("\n".join(kept) + ("\n" if kept else ""), encoding="utf-8")
        return removed

    @staticmethod
    def _should_remove_record(record: dict, keyword: str, target_dates: set[str] | None) -> bool:
        content = str(record.get("content", ""))
        date = str(record.get("date", ""))
        if target_dates is not None and date not in target_dates:
            return False
        return keyword in content


SHORT_TERM_HINTS = (
    "剛剛",
    "剛才",
    "前面",
    "上一句",
    "上句",
    "剛剛說",
    "剛才說",
    "剛剛講",
    "剛才講",
)


def is_short_term_query(text: str) -> bool:
    return any(keyword in text for keyword in SHORT_TERM_HINTS)


def search_session_messages(
    messages: Sequence[str],
    query: str,
    max_items: int = 5,
) -> List[str]:
    if not messages:
        return []
    cleaned = _strip_short_term_hints(query)
    if cleaned:
        matched = [msg for msg in messages if cleaned in msg]
        if matched:
            return matched[-max_items:]
    return list(messages)[-max_items:]


def _strip_short_term_hints(text: str) -> str:
    cleaned = text
    for keyword in SHORT_TERM_HINTS:
        cleaned = cleaned.replace(keyword, "")
    return cleaned.strip(" ：:，,。.!？?　")
