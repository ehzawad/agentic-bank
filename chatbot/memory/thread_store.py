from __future__ import annotations

from datetime import datetime, timezone

from chatbot.memory.models import ConversationThread, ThreadStatus


class ThreadStore:
    """Tracks conversation topics: active, suspended, resolved."""

    def __init__(self) -> None:
        self._threads: list[ConversationThread] = []

    def create(self, topic: str, **kwargs) -> ConversationThread:
        thread = ConversationThread(topic=topic, **kwargs)
        self._threads.append(thread)
        return thread

    def get_active(self) -> list[ConversationThread]:
        return [t for t in self._threads if t.status == ThreadStatus.ACTIVE]

    def get_suspended(self) -> list[ConversationThread]:
        return [t for t in self._threads if t.status == ThreadStatus.SUSPENDED]

    def get_by_topic(self, topic: str) -> ConversationThread | None:
        for t in reversed(self._threads):
            if t.topic == topic and t.status in (ThreadStatus.ACTIVE, ThreadStatus.SUSPENDED):
                return t
        return None

    def suspend(self, thread_id: str) -> None:
        for t in self._threads:
            if t.thread_id == thread_id:
                t.status = ThreadStatus.SUSPENDED
                t.suspended_at = datetime.now(timezone.utc)
                return

    def resume(self, thread_id: str) -> None:
        for t in self._threads:
            if t.thread_id == thread_id:
                t.status = ThreadStatus.ACTIVE
                t.suspended_at = None
                return

    def resolve(self, thread_id: str) -> None:
        for t in self._threads:
            if t.thread_id == thread_id:
                t.status = ThreadStatus.RESOLVED
                t.resolved_at = datetime.now(timezone.utc)
                return

    def to_context(self) -> str:
        active = self.get_active()
        suspended = self.get_suspended()
        if not active and not suspended:
            return ""
        lines = []
        for t in active:
            line = f"- [{t.status.value}] {t.topic}"
            if t.workflow_id:
                line += f" (workflow step {t.workflow_step})"
            if t.slots_needed:
                line += f" — need: {', '.join(t.slots_needed)}"
            if t.slots_filled:
                filled = ", ".join(f"{k}={v}" for k, v in t.slots_filled.items())
                line += f" — have: {filled}"
            lines.append(line)
        for t in suspended:
            line = f"- [{t.status.value}] {t.topic}"
            if t.slots_needed:
                line += f" — need: {', '.join(t.slots_needed)}"
            lines.append(line)
        return "\n".join(lines)
