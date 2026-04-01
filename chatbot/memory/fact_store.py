from __future__ import annotations

from chatbot.memory.models import Fact


class FactStore:
    """Stores ground-truth facts from tool results only.

    Versioned: corrections create new entries with superseded_by links.
    """

    def __init__(self) -> None:
        self._facts: list[Fact] = []

    def write(self, key: str, value: object, source_tool: str, turn_number: int) -> Fact:
        for f in self._facts:
            if f.key == key and f.superseded_by is None:
                new_fact = Fact(
                    key=key,
                    value=value,
                    source_tool=source_tool,
                    turn_number=turn_number,
                )
                f.superseded_by = new_fact.fact_id
                self._facts.append(new_fact)
                return new_fact

        fact = Fact(key=key, value=value, source_tool=source_tool, turn_number=turn_number)
        self._facts.append(fact)
        return fact

    def get_current(self) -> list[Fact]:
        return [f for f in self._facts if f.superseded_by is None]

    def get_all(self) -> list[Fact]:
        return list(self._facts)

    def mark_presented(self) -> None:
        """Mark all current facts as already communicated to the customer."""
        for f in self._facts:
            if f.superseded_by is None:
                f.presented = True

    def to_context(self) -> str:
        current = self.get_current()
        if not current:
            return ""
        new_facts = [f for f in current if not f.presented]
        old_facts = [f for f in current if f.presented]
        lines = []
        if new_facts:
            lines.append("[NEW — present to customer]")
            for f in new_facts:
                lines.append(f"- {f.key}: {f.value} (via {f.source_tool})")
        if old_facts:
            lines.append("[ALREADY COMMUNICATED — do NOT repeat]")
            for f in old_facts:
                lines.append(f"- {f.source_tool} results")
        return "\n".join(lines)
