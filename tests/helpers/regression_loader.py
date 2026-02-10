from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import List


@dataclass(frozen=True)
class RegressionCase:
    case_id: str
    category: str
    input_text: str
    expected_behavior: str
    priority: str


def _load_json(path: Path) -> list[dict]:
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    if not isinstance(data, list):
        return []
    return [item for item in data if isinstance(item, dict)]


def load_regression_cases(base_dir: Path) -> List[RegressionCase]:
    path = base_dir / "tests" / "data" / "regression_cases.json"
    cases: List[RegressionCase] = []
    for item in _load_json(path):
        case_id = str(item.get("case_id", "")).strip()
        category = str(item.get("category", "")).strip()
        input_text = str(item.get("input_text", "")).strip()
        expected_behavior = str(item.get("expected_behavior", "")).strip()
        priority = str(item.get("priority", "")).strip()
        if not case_id or not category or not input_text:
            continue
        cases.append(
            RegressionCase(
                case_id=case_id,
                category=category,
                input_text=input_text,
                expected_behavior=expected_behavior,
                priority=priority or "P2",
            )
        )
    return cases


def load_chinese_phrases(base_dir: Path) -> List[dict]:
    path = base_dir / "tests" / "data" / "chinese_phrases.json"
    return _load_json(path)
