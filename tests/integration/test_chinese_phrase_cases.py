from __future__ import annotations

from datetime import datetime
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dongdong_bot.agent.schedule_parser import ScheduleParser
from dongdong_bot.main import _has_memory_keywords, _is_explicit_memory_save
from tests.helpers.regression_loader import load_chinese_phrases


def test_chinese_phrase_cases():
    cases = load_chinese_phrases(ROOT)
    assert cases, "常見中文句型測試集不可為空"

    parser = ScheduleParser()
    now = datetime(2026, 2, 5, 9, 0)

    for case in cases:
        phrase = str(case.get("phrase", "")).strip()
        expected = str(case.get("expected", "")).strip()
        assert phrase
        if expected == "schedule_add":
            command = parser.parse(phrase, now=now)
            assert command is not None
            assert command.action == "add"
            assert command.start_time is not None
        elif expected == "memory_save":
            assert _is_explicit_memory_save(phrase)
        elif expected == "memory_query":
            assert _has_memory_keywords(phrase)
        else:
            raise AssertionError(f"未知的預期類型: {expected}")
