import sys
from pathlib import Path
from datetime import datetime

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


@pytest.fixture()
def fixed_now() -> datetime:
    return datetime(2024, 1, 2, 3, 4, 5)


@pytest.fixture()
def patch_report_writer_now(monkeypatch, fixed_now):
    from dongdong_bot.lib import report_writer

    class FixedDatetime(datetime):
        @classmethod
        def now(cls, tz=None):  # noqa: ANN001
            return fixed_now

    monkeypatch.setattr(report_writer, "datetime", FixedDatetime)
    return fixed_now
