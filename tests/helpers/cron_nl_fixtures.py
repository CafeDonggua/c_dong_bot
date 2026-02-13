from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
from typing import Any


@dataclass(frozen=True)
class CronNLCase:
    name: str
    text: str
    expected_route: str
    expected_schedule_kind: str | None = None
    expected_schedule_value: str | None = None
    expected_title: str | None = None


def load_cron_nl_cases() -> list[CronNLCase]:
    repo_root = Path(__file__).resolve().parents[2]
    path = repo_root / "tests" / "data" / "cron_nl_cases.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("cron_nl_cases.json 必須為陣列")
    items: list[CronNLCase] = []
    for raw in payload:
        if not isinstance(raw, dict):
            continue
        items.append(_to_case(raw))
    return items


def _to_case(raw: dict[str, Any]) -> CronNLCase:
    return CronNLCase(
        name=str(raw.get("name", "")).strip(),
        text=str(raw.get("text", "")).strip(),
        expected_route=str(raw.get("expected_route", "")).strip(),
        expected_schedule_kind=_optional_text(raw.get("expected_schedule_kind")),
        expected_schedule_value=_optional_text(raw.get("expected_schedule_value")),
        expected_title=_optional_text(raw.get("expected_title")),
    )


def _optional_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
