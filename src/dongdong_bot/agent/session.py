from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List


@dataclass
class Session:
    user_id: str
    started_at: datetime
    last_active_at: datetime
    messages: List[str] = field(default_factory=list)
    pending_action: str | None = None
    pending_payload: Dict[str, str | int] = field(default_factory=dict)


class SessionStore:
    def __init__(self, ttl_minutes: int = 30, max_messages: int = 20) -> None:
        self.ttl = timedelta(minutes=ttl_minutes)
        self.max_messages = max_messages
        self._sessions: Dict[str, Session] = {}

    def touch(self, user_id: str, text: str) -> Session:
        now = datetime.now()
        session = self._sessions.get(user_id)
        if session is None or now - session.last_active_at > self.ttl:
            session = Session(user_id=user_id, started_at=now, last_active_at=now)
            self._sessions[user_id] = session
        session.last_active_at = now
        if text.strip():
            session.messages.append(text.strip())
            if len(session.messages) > self.max_messages:
                session.messages = session.messages[-self.max_messages :]
        return session

    def get(self, user_id: str) -> Session | None:
        session = self._sessions.get(user_id)
        if session is None:
            return None
        if datetime.now() - session.last_active_at > self.ttl:
            self._sessions.pop(user_id, None)
            return None
        return session

    def clear(self, user_id: str) -> None:
        self._sessions.pop(user_id, None)

    def set_pending_action(
        self,
        user_id: str,
        action: str,
        payload: Dict[str, str | int] | None = None,
    ) -> None:
        session = self.get(user_id)
        if session is None:
            session = self.touch(user_id, "")
        session.pending_action = action
        session.pending_payload = dict(payload or {})

    def get_pending_action(self, user_id: str) -> tuple[str | None, Dict[str, str | int]]:
        session = self.get(user_id)
        if session is None:
            return None, {}
        return session.pending_action, dict(session.pending_payload)

    def clear_pending_action(self, user_id: str) -> None:
        session = self.get(user_id)
        if session is None:
            return
        session.pending_action = None
        session.pending_payload = {}
