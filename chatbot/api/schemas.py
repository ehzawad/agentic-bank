from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class CreateSessionResponse(BaseModel):
    session_id: str
    greeting: str


class ChatRequest(BaseModel):
    session_id: str
    message: str


class ChatResponse(BaseModel):
    response: str
    state: str
    emotion: str
    tool_calls: list[dict[str, Any]] = []
    transferred_to_human: bool = False


class SessionStateResponse(BaseModel):
    session_id: str
    state: str
    verified: bool
    customer_name: str | None = None
    facts: list[dict[str, Any]] = []
    threads: list[dict[str, Any]] = []
    emotion_trajectory: list[str] = []


class HealthResponse(BaseModel):
    status: str = "ok"
    model: str = ""
