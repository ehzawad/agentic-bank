from __future__ import annotations

import re

from chatbot.memory.models import EmotionReading, EmotionState

# Negative lexicon for emotion scoring
_NEGATIVE_WORDS = frozenset({
    "angry", "furious", "frustrated", "upset", "terrible", "horrible",
    "unacceptable", "ridiculous", "disgusting", "awful", "worst",
    "hate", "stupid", "incompetent", "useless", "pathetic",
    "scam", "fraud", "stolen", "unauthorized", "lost", "panic",
    "emergency", "urgent", "immediately", "asap", "hurry",
})

_URGENCY_PHRASES = [
    "right now", "right away", "this instant", "how many times",
    "third time", "called before", "nobody", "no one",
]


def _score_text(text: str) -> tuple[float, str, list[str]]:
    """Heuristic emotion scoring. Returns (score, label, indicators)."""
    indicators: list[str] = []
    score = 0.0

    # Caps ratio
    alpha_chars = [c for c in text if c.isalpha()]
    if alpha_chars:
        caps_ratio = sum(1 for c in alpha_chars if c.isupper()) / len(alpha_chars)
        if caps_ratio > 0.5:
            score += 0.3
            indicators.append(f"caps_ratio={caps_ratio:.2f}")

    # Exclamation density
    excl_count = text.count("!")
    if excl_count >= 3:
        score += 0.2
        indicators.append(f"exclamations={excl_count}")
    elif excl_count >= 1:
        score += 0.1

    # Negative lexicon
    words = set(re.findall(r"[a-z]+", text.lower()))
    neg_hits = words & _NEGATIVE_WORDS
    if neg_hits:
        score += min(0.3, len(neg_hits) * 0.1)
        indicators.append(f"neg_words={','.join(sorted(neg_hits))}")

    # Urgency phrases
    lower = text.lower()
    for phrase in _URGENCY_PHRASES:
        if phrase in lower:
            score += 0.15
            indicators.append(f"urgency='{phrase}'")

    score = min(1.0, score)

    # Label
    if score >= 0.8:
        label = "furious"
    elif score >= 0.65:
        label = "angry"
    elif score >= 0.5:
        label = "stressed"
    elif score >= 0.35:
        label = "anxious"
    elif score >= 0.2:
        label = "concerned"
    else:
        label = "neutral"

    return score, label, indicators


class EmotionStore:
    def __init__(self) -> None:
        self._state = EmotionState()

    @property
    def state(self) -> EmotionState:
        return self._state

    def score_turn(self, text: str, turn_number: int) -> EmotionReading:
        score, label, indicators = _score_text(text)
        reading = EmotionReading(
            turn_number=turn_number,
            score=score,
            label=label,
            indicators=indicators,
        )
        self._state.readings.append(reading)
        return reading

    def mark_escalation_triggered(self) -> None:
        self._state.escalation_triggered = True

    def to_context(self) -> str:
        if not self._state.readings:
            return ""
        labels = [r.label for r in self._state.readings[-5:]]
        trajectory = " -> ".join(labels)
        current = self._state.current
        lines = [f"Trajectory: {trajectory}", f"Current: {current.label} ({current.score:.2f})"]
        if self._state.trajectory_rising and current and current.score >= 0.5:
            lines.append("WARNING: Customer emotion is rising. Lead with empathy.")
        if self._state.escalation_triggered:
            lines.append("ESCALATION: Human transfer has been offered.")
        return "\n".join(lines)
