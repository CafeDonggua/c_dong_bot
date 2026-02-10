from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import re
from typing import Iterable, List, Tuple

from dongdong_bot.config import PROJECT_ROOT


CHAT_KEYWORDS = ("聊天", "對話", "回覆", "語意", "語音", "chat")
SCHEDULE_KEYWORDS = ("行程", "提醒", "排程", "schedule", "reminder")


@dataclass
class ChecklistItem:
    priority: str
    text: str
    status: str
    reference: str


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _extract_bullets(text: str) -> List[str]:
    lines: List[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("- "):
            lines.append(stripped[2:].strip())
        elif stripped.startswith("* "):
            lines.append(stripped[2:].strip())
    return lines


def _extract_readme_features(readme_path: Path) -> List[str]:
    if not readme_path.exists():
        return []
    return _extract_bullets(_read_text(readme_path))


def _classify_features(lines: Iterable[str]) -> Tuple[List[str], List[str]]:
    chat: List[str] = []
    schedule: List[str] = []
    for line in lines:
        if any(keyword in line for keyword in SCHEDULE_KEYWORDS):
            schedule.append(line)
        if any(keyword in line for keyword in CHAT_KEYWORDS):
            chat.append(line)
    return chat, schedule


def _scan_schedule_files(base_dir: Path) -> List[str]:
    results: List[str] = []
    if not base_dir.exists():
        return results
    for path in base_dir.rglob("*"):
        if not path.is_file():
            continue
        name = path.name.lower()
        if "schedule" in name or "reminder" in name:
            results.append(str(path.relative_to(base_dir)))
        if len(results) >= 50:
            break
    return results


def _tokenize(text: str) -> List[str]:
    tokens = re.findall(r"[A-Za-z0-9]{2,}|[\u4e00-\u9fff]{2,}", text)
    return tokens


def _match_any(tokens: Iterable[str], candidates: Iterable[str]) -> bool:
    for token in tokens:
        for line in candidates:
            if token in line:
                return True
    return False


def _parse_checklist(checklist_path: Path, c_dong_features: List[str], nanobot_features: List[str]) -> List[ChecklistItem]:
    items: List[ChecklistItem] = []
    priority = ""
    for line in _read_text(checklist_path).splitlines():
        stripped = line.strip()
        if stripped.startswith("## "):
            if "必要條件" in stripped:
                priority = "v1.0 必要"
            elif "建議條件" in stripped:
                priority = "v1.0 建議"
            elif "可選條件" in stripped:
                priority = "v1.0 可選"
            else:
                priority = ""
            continue
        if stripped.startswith("- "):
            text = stripped[2:].strip()
            tokens = _tokenize(text)
            in_c_dong = _match_any(tokens, c_dong_features)
            in_nanobot = _match_any(tokens, nanobot_features)
            if in_c_dong:
                status = "已具備"
                reference = "c_dong_bot README"
            elif in_nanobot:
                status = "缺口"
                reference = "nanobot 功能"
            else:
                status = "需開發"
                reference = "-"
            items.append(ChecklistItem(priority=priority or "未分類", text=text, status=status, reference=reference))
    return items


def _render_report(
    nanobot_path: Path,
    checklist_path: Path,
    chat_features: List[str],
    schedule_features: List[str],
    schedule_files: List[str],
    checklist_items: List[ChecklistItem],
) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines: List[str] = []
    lines.append("# Nanobot 功能對照報告")
    lines.append("")
    lines.append(f"- 產生時間：{now}")
    lines.append(f"- Nanobot 路徑：{nanobot_path}")
    lines.append(f"- Checklist 路徑：{checklist_path}")
    lines.append("")
    lines.append("> 狀態為自動比對結果，需人工確認。")
    lines.append("")

    lines.append("## Nanobot 聊天功能")
    if chat_features:
        lines.extend(f"- {item}" for item in chat_features)
    else:
        lines.append("- （未偵測到）")
    lines.append("")

    lines.append("## Nanobot 排程功能")
    if schedule_features:
        lines.extend(f"- {item}" for item in schedule_features)
    else:
        lines.append("- （未偵測到）")
    lines.append("")

    lines.append("## Nanobot 排程相關檔案")
    if schedule_files:
        lines.extend(f"- {item}" for item in schedule_files)
    else:
        lines.append("- （未偵測到）")
    lines.append("")

    must_items = [item for item in checklist_items if item.priority == "v1.0 必要"]
    status_counts = {
        "已具備": sum(1 for item in must_items if item.status == "已具備"),
        "缺口": sum(1 for item in must_items if item.status == "缺口"),
        "需開發": sum(1 for item in must_items if item.status == "需開發"),
    }

    lines.append("## v1.0 必要條件摘要統計")
    lines.append(f"- 已具備：{status_counts['已具備']}")
    lines.append(f"- 缺口：{status_counts['缺口']}")
    lines.append(f"- 需開發：{status_counts['需開發']}")
    lines.append("")

    lines.append("## VERSION_1_0_CHECKLIST 對照")
    lines.append("| 項目 | 優先等級 | 狀態 | 參考 |")
    lines.append("|------|----------|------|------|")
    for item in checklist_items:
        lines.append(f"| {item.text} | {item.priority} | {item.status} | {item.reference} |")
    lines.append("")

    lines.append("## v1.0 優先項目摘要")
    if must_items:
        for item in must_items:
            lines.append(f"- [{item.status}] {item.text}")
    else:
        lines.append("- （未偵測到）")

    lines.append("")
    lines.append("## 人工複核清單")
    lines.append("- 確認 Nanobot 排程相關檔案列表是否完整")
    lines.append("- 確認 checklist 對照狀態是否正確")
    lines.append("- 補充已具備項目的證據來源（文件或測試）")

    return "\n".join(lines) + "\n"


def build_report(
    *,
    nanobot_path: Path,
    checklist_path: Path,
    output_dir: Path,
    project_root: Path,
) -> Path:
    if not nanobot_path.exists():
        raise FileNotFoundError(f"找不到 Nanobot 路徑: {nanobot_path}")
    if not checklist_path.exists():
        raise FileNotFoundError(f"找不到 checklist: {checklist_path}")

    readme_path = nanobot_path / "README.md"
    nanobot_bullets = _extract_bullets(_read_text(readme_path)) if readme_path.exists() else []
    chat_features, schedule_features = _classify_features(nanobot_bullets)
    schedule_files = _scan_schedule_files(nanobot_path)

    c_dong_readme = project_root / "README.md"
    c_dong_features = _extract_readme_features(c_dong_readme)

    nanobot_features = chat_features + schedule_features
    checklist_items = _parse_checklist(checklist_path, c_dong_features, nanobot_features)

    report_text = _render_report(
        nanobot_path=nanobot_path,
        checklist_path=checklist_path,
        chat_features=chat_features,
        schedule_features=schedule_features,
        schedule_files=schedule_files,
        checklist_items=checklist_items,
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    filename = f"nanobot-compare-{datetime.now().strftime('%Y%m%d')}.md"
    report_path = output_dir / filename
    report_path.write_text(report_text, encoding="utf-8")
    return report_path


def parse_args() -> argparse.Namespace:
    default_nanobot = PROJECT_ROOT / "_ext" / "nanobot"
    default_checklist = PROJECT_ROOT / "VERSION_1_0_CHECKLIST.md"
    default_output = PROJECT_ROOT / "data" / "reports"

    parser = argparse.ArgumentParser(description="產出 Nanobot 功能對照報告")
    parser.add_argument("--nanobot-path", default=str(default_nanobot), help="Nanobot 專案路徑")
    parser.add_argument("--checklist-path", default=str(default_checklist), help="VERSION_1_0_CHECKLIST.md 路徑")
    parser.add_argument("--output-dir", default=str(default_output), help="報告輸出資料夾")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        report_path = build_report(
            nanobot_path=Path(args.nanobot_path),
            checklist_path=Path(args.checklist_path),
            output_dir=Path(args.output_dir),
            project_root=PROJECT_ROOT,
        )
    except FileNotFoundError as exc:
        print(f"錯誤：{exc}")
        return 1
    print(f"報告已產生：{report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
