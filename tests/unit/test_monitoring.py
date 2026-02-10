from __future__ import annotations

from datetime import datetime, timedelta

from dongdong_bot.monitoring import Monitoring


class FakeClock:
    def __init__(self, start: datetime) -> None:
        self.current = start

    def now(self) -> datetime:
        return self.current

    def advance(self, seconds: int) -> None:
        self.current += timedelta(seconds=seconds)


def test_startup_emits_single_line() -> None:
    outputs: list[str] = []
    clock = FakeClock(datetime(2026, 2, 2, 16, 30, 0))
    monitoring = Monitoring(
        heartbeat_interval_seconds=1800,
        error_throttle_seconds=60,
        now_fn=clock.now,
        output=outputs.append,
    )

    monitoring.startup()

    assert len(outputs) == 1
    assert "[startup]" in outputs[0]
    assert "正常運行" in outputs[0]
    assert outputs[0].startswith("[2026-02-02 16:30:00]")


def test_error_throttle_suppresses_duplicates() -> None:
    outputs: list[str] = []
    clock = FakeClock(datetime(2026, 2, 2, 16, 0, 0))
    monitoring = Monitoring(
        heartbeat_interval_seconds=1800,
        error_throttle_seconds=60,
        now_fn=clock.now,
        output=outputs.append,
    )

    class SampleError(RuntimeError):
        pass

    monitoring.error(SampleError("boom"))
    monitoring.error(SampleError("boom"))
    assert len(outputs) == 1

    clock.advance(61)
    monitoring.error(SampleError("boom"))

    assert len(outputs) == 2
    assert "SampleError" in outputs[1]
    assert "抑制 1 次" in outputs[1]
