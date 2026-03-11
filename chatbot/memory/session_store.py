from __future__ import annotations

from chatbot.memory.models import CustomerSession


class SessionStore:
    """In-memory session store for a single conversation session."""

    def __init__(self) -> None:
        self._session: CustomerSession | None = None

    @property
    def session(self) -> CustomerSession | None:
        return self._session

    @property
    def is_verified(self) -> bool:
        return self._session is not None and self._session.verified

    def create(self, session_id: str | None = None) -> CustomerSession:
        self._session = CustomerSession(session_id=session_id) if session_id else CustomerSession()
        return self._session

    def write(self, data: dict) -> None:
        if self._session is None:
            self._session = CustomerSession()
        for key, value in data.items():
            if hasattr(self._session, key):
                setattr(self._session, key, value)
            else:
                self._session.extra[key] = value

    def to_context(self) -> str:
        s = self._session
        if s is None or not s.verified:
            return ""
        lines = [
            f"Name: {s.customer_name}",
            f"Segment: {s.segment}",
            f"Tenure: {s.tenure}",
            f"Accounts: {', '.join(s.accounts)}",
            f"Cards: {', '.join(s.cards) if s.cards else 'none on file'}",
        ]
        if s.extra:
            for k, v in s.extra.items():
                lines.append(f"{k}: {v}")
        return "\n".join(lines)
