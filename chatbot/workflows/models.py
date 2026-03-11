from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class StepType(str, Enum):
    AUTO = "auto"
    NEEDS_INPUT = "needs_input"
    PROACTIVE = "proactive"
    CONFIRM = "confirm"


class SlotSpec(BaseModel):
    name: str
    description: str
    required: bool = True


class WorkflowStep(BaseModel):
    step_id: str
    step_type: StepType
    description: str
    slots_needed: list[SlotSpec] = Field(default_factory=list)
    tool_to_call: str | None = None
    prompt_template: str | None = None


class WorkflowDefinition(BaseModel):
    workflow_id: str
    name: str
    steps: list[WorkflowStep]
    timeout_minutes: int = 30
