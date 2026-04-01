from __future__ import annotations

from typing import Any

from chatbot.memory.models import Turn


class TurnStore:
    """Stores conversation turns in Anthropic API message format."""

    def __init__(self, max_turns: int = 100) -> None:
        self._turns: list[Turn] = []
        self._turn_counter: int = 0
        self._max_turns = max_turns

    @property
    def turn_number(self) -> int:
        return self._turn_counter

    def append(self, role: str, content: Any) -> Turn:
        self._turn_counter += 1
        turn = Turn(turn_number=self._turn_counter, role=role, content=content)
        self._turns.append(turn)
        # Evict oldest if over limit
        if len(self._turns) > self._max_turns:
            self._turns = self._turns[-self._max_turns :]
        return turn

    def get_messages(self) -> list[dict[str, Any]]:
        """Return turns as Anthropic API messages format."""
        messages: list[dict[str, Any]] = []
        for turn in self._turns:
            messages.append({"role": turn.role, "content": turn.content})
        return messages

    def clear(self) -> None:
        self._turns.clear()
        self._turn_counter = 0

    def get_recent(self, n: int = 10) -> list[Turn]:
        return self._turns[-n:]
