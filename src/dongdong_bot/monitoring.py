from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from threading import Lock
from typing import Callable, Dict


@dataclass
class _ErrorState:
    last_emitted: datetime
    suppressed_count: int = 0


class Monitoring:
    def __init__(
        self,
        heartbeat_interval_seconds: int,
        error_throttle_seconds: int,
        now_fn: Callable[[], datetime] | None = None,
        output: Callable[[str], None] | None = None,
    ) -> None:
        self.heartbeat_interval_seconds = heartbeat_interval_seconds
        self.error_throttle_seconds = error_throttle_seconds
        self._now_fn = now_fn or datetime.now
        self._output = output or print
        self._lock = Lock()
        self._error_states: Dict[str, _ErrorState] = {}

    def startup(self) -> None:
        self._emit("startup", "正常運行")

    def received(self) -> None:
        self._emit("received", "已收到訊息")

    def replied(self) -> None:
        self._emit("replied", "已完成回覆")

    def info(self, message: str) -> None:
        self._emit("info", message)

    def heartbeat(self) -> None:
        self._emit("heartbeat", "仍在運行")

    def error(self, exc: BaseException) -> None:
        now = self._now_fn()
        signature = exc.__class__.__name__
        suppressed = 0
        with self._lock:
            state = self._error_states.get(signature)
            if state is not None:
                elapsed = (now - state.last_emitted).total_seconds()
                if elapsed < self.error_throttle_seconds:
                    state.suppressed_count += 1
                    return
                suppressed = state.suppressed_count
            self._error_states[signature] = _ErrorState(last_emitted=now)
        self._emit("error", signature, suppressed_count=suppressed)

    def error_event(self, event_type: str, message: str) -> None:
        cleaned = f"{event_type} {message}".strip()
        self._emit("error_event", cleaned)

    def perf(self, name: str, elapsed_ms: float, detail: str | None = None) -> None:
        cleaned = f"{name} {elapsed_ms:.1f}ms"
        if detail:
            cleaned = f"{cleaned} {detail}"
        self._emit("perf", cleaned)

    def route(self, target: str, reason: str, detail: str | None = None) -> None:
        cleaned = f"target={target} reason={reason}"
        if detail:
            cleaned = f"{cleaned} {detail}"
        self._emit("route", cleaned)

    def _emit(self, event_type: str, summary: str, suppressed_count: int = 0) -> None:
        timestamp = self._now_fn()
        cleaned = self._sanitize(summary)
        if suppressed_count:
            cleaned = f"{cleaned} (抑制 {suppressed_count} 次)"
        line = f"[{timestamp:%Y-%m-%d %H:%M:%S}] [{event_type}] {cleaned}"
        self._output(line)

    @staticmethod
    def _sanitize(text: str) -> str:
        single_line = " ".join(text.replace("\r", " ").replace("\n", " ").split())
        return single_line[:200]
