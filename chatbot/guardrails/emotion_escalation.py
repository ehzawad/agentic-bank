"""G5: Emotion Escalation.

Triggers proactive human transfer offer when customer anger rises over 3+ turns.
"""

from __future__ import annotations

from dataclasses import dataclass

from chatbot.config import settings
from chatbot.memory.models import EmotionState


@dataclass
class EscalationResult:
    should_escalate: bool = False
    instruction: str = ""


class EmotionEscalation:
    def check(self, state: EmotionState) -> EscalationResult:
        if state.escalation_triggered:
            return EscalationResult(should_escalate=False)

        readings = state.readings
        n = settings.emotion_escalation_turns
        threshold = settings.emotion_escalation_threshold

        if len(readings) < n:
            return EscalationResult(should_escalate=False)

        recent = readings[-n:]

        is_rising = all(
            recent[i].score <= recent[i + 1].score for i in range(len(recent) - 1)
        )
        is_high = recent[-1].score >= threshold

        if is_rising and is_high:
            labels = " -> ".join(r.label for r in recent)
            return EscalationResult(
                should_escalate=True,
                instruction=(
                    f"The customer has been increasingly upset for {n} turns "
                    f"(trajectory: {labels}). "
                    "Proactively offer to transfer them to a human agent."
                ),
            )

        return EscalationResult(should_escalate=False)
