from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import re
from typing import List


@dataclass
class ReportWriter:
    base_dir: str

    def write(self, title: str, summary: str, bullets: List[str], sources: List[str]) -> Path:
        base = Path(self.base_dir)
        base.mkdir(parents=True, exist_ok=True)
        safe_title = self._slugify(title) or "report"
        date_prefix = datetime.now().strftime("%Y-%m-%d")
        path = base / f"{date_prefix}-{safe_title}.md"
        bullets_block = "\n".join(f"- {item}" for item in bullets)
        sources_block = "\n".join(f"- {item}" for item in sources)
        content = (
            f"# {title}\n\n"
            "## 摘要\n"
            f"{summary}\n\n"
            "## 重點\n"
            f"{bullets_block}\n\n"
            "## 來源\n"
            f"{sources_block}\n"
        )
        path.write_text(content, encoding="utf-8")
        return path

    @staticmethod
    def _slugify(value: str) -> str:
        cleaned = re.sub(r"[\\s]+", "-", value.strip())
        cleaned = re.sub(r"[^\w\\-\\u4e00-\\u9fff]", "", cleaned)
        return cleaned[:80].strip("-")
