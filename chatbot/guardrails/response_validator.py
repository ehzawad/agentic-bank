"""Orchestrates all guardrails on the final response."""

from __future__ import annotations

from chatbot.guardrails.hallucination_blocker import HallucinationBlocker, ScanResult
from chatbot.guardrails.emotion_escalation import EmotionEscalation, EscalationResult
from chatbot.memory.models import EmotionState, Fact


class ResponseValidator:
    def __init__(self) -> None:
        self.hallucination_blocker = HallucinationBlocker()
        self.emotion_escalation = EmotionEscalation()

    def validate(
        self,
        response_text: str,
        fact_entries: list[Fact],
        emotion_state: EmotionState,
    ) -> tuple[ScanResult, EscalationResult]:
        g1 = self.hallucination_blocker.scan(response_text, fact_entries)
        g5 = self.emotion_escalation.check(emotion_state)
        return g1, g5
