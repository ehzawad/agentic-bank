from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _new_id() -> str:
    return uuid.uuid4().hex[:12]


# ---------------------------------------------------------------------------
# Session Store
# ---------------------------------------------------------------------------

class CustomerSession(BaseModel):
    session_id: str = Field(default_factory=_new_id)
    customer_name: str | None = None
    customer_id: str | None = None
    accounts: list[str] = Field(default_factory=list)
    cards: list[str] = Field(default_factory=list)
    segment: str | None = None
    tenure: str | None = None
    verified: bool = False
    verified_at: datetime | None = None
    auth_attempts: int = 0
    extra: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=_utcnow)


# ---------------------------------------------------------------------------
# Fact Store
# ---------------------------------------------------------------------------

class Fact(BaseModel):
    fact_id: str = Field(default_factory=_new_id)
    key: str
    value: Any
    source_tool: str
    turn_number: int
    timestamp: datetime = Field(default_factory=_utcnow)
    superseded_by: str | None = None
    presented: bool = False


# ---------------------------------------------------------------------------
# Thread Store
# ---------------------------------------------------------------------------

class ThreadStatus(str, Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    RESOLVED = "resolved"
    EXPIRED = "expired"


class ConversationThread(BaseModel):
    thread_id: str = Field(default_factory=_new_id)
    topic: str
    status: ThreadStatus = ThreadStatus.ACTIVE
    workflow_id: str | None = None
    workflow_step: int | None = None
    slots_filled: dict[str, Any] = Field(default_factory=dict)
    slots_needed: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=_utcnow)
    suspended_at: datetime | None = None
    resolved_at: datetime | None = None


# ---------------------------------------------------------------------------
# Emotion Store
# ---------------------------------------------------------------------------

class EmotionReading(BaseModel):
    turn_number: int
    score: float  # 0.0 (calm) to 1.0 (furious)
    label: str
    indicators: list[str] = Field(default_factory=list)


class EmotionState(BaseModel):
    readings: list[EmotionReading] = Field(default_factory=list)
    escalation_triggered: bool = False

    @property
    def current(self) -> EmotionReading | None:
        return self.readings[-1] if self.readings else None

    @property
    def trajectory_rising(self) -> bool:
        if len(self.readings) < 3:
            return False
        recent = self.readings[-3:]
        return all(recent[i].score <= recent[i + 1].score for i in range(2))


# ---------------------------------------------------------------------------
# Turn Store
# ---------------------------------------------------------------------------

class Turn(BaseModel):
    turn_number: int
    role: str  # "user" or "assistant"
    content: Any  # string or list of content blocks
    timestamp: datetime = Field(default_factory=_utcnow)
