from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import re
from typing import List

from dongdong_bot.lib.report_content import ReportContent


@dataclass
class ReportWriter:
    base_dir: str

    def write(
        self,
        title: str,
        content: ReportContent,
        *,
        query_text: str | None = None,
        query_time: datetime | None = None,
    ) -> Path:
        base = Path(self.base_dir)
        base.mkdir(parents=True, exist_ok=True)
        safe_title = self._slugify(title) or "report"
        date_prefix = datetime.now().strftime("%Y-%m-%d")
        path = base / f"{date_prefix}-{safe_title}.md"
        bullets_block = "\n".join(f"- {item}" for item in content.bullets)
        sources_block = "\n".join(f"- {item}" for item in content.sources)
        meta_block = self._format_meta(query_text, query_time)
        report_text = (
            f"# {title}\n\n"
            f"{meta_block}"
            "## 摘要\n"
            f"{content.summary}\n\n"
            "## 重點\n"
            f"{bullets_block}\n\n"
            "## 來源\n"
            f"{sources_block}\n"
        )
        path.write_text(report_text, encoding="utf-8")
        return path

    @staticmethod
    def _slugify(value: str) -> str:
        cleaned = re.sub(r"[\\s]+", "-", value.strip())
        cleaned = re.sub(r"[^\w\\-\\u4e00-\\u9fff]", "", cleaned)
        return cleaned[:80].strip("-")

    @staticmethod
    def _format_meta(query_text: str | None, query_time: datetime | None) -> str:
        if not query_text and not query_time:
            return ""
        parts: List[str] = []
        if query_text:
            parts.append(f"- 查詢文字：{query_text}")
        if query_time:
            parts.append(f"- 查詢時間：{query_time.strftime('%Y-%m-%d %H:%M:%S')}")
        return "## 查詢資訊\n" + "\n".join(parts) + "\n\n"
