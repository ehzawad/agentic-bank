"""Workflow engine: step execution, suspend/resume, slot filling."""

from __future__ import annotations

from chatbot.memory.models import ConversationThread, ThreadStatus
from chatbot.memory.thread_store import ThreadStore
from chatbot.workflows.models import WorkflowDefinition


class WorkflowEngine:
    def __init__(self, definitions: dict[str, WorkflowDefinition] | None = None) -> None:
        self._definitions = definitions or {}

    def register(self, definition: WorkflowDefinition) -> None:
        self._definitions[definition.workflow_id] = definition

    def has_workflow(self, workflow_id: str) -> bool:
        return workflow_id in self._definitions

    def start(
        self,
        workflow_id: str,
        thread_store: ThreadStore,
        initial_slots: dict | None = None,
    ) -> ConversationThread:
        defn = self._definitions[workflow_id]
        first_step = defn.steps[0]
        needed = [
            s.name for s in first_step.slots_needed
            if s.name not in (initial_slots or {})
        ]
        thread = thread_store.create(
            topic=workflow_id,
            workflow_id=workflow_id,
            workflow_step=0,
            slots_filled=initial_slots or {},
            slots_needed=needed,
        )
        return thread

    def get_definition(self, workflow_id: str) -> WorkflowDefinition | None:
        return self._definitions.get(workflow_id)

    def advance(self, thread: ConversationThread, new_slots: dict | None = None) -> bool:
        """Fill slots and advance to next step if current step is complete.

        Returns True if workflow is complete.
        """
        defn = self._definitions.get(thread.workflow_id or "")
        if defn is None:
            return True

        if new_slots:
            thread.slots_filled.update(new_slots)

        current_step = defn.steps[thread.workflow_step or 0]
        still_needed = [
            s.name for s in current_step.slots_needed
            if s.required and s.name not in thread.slots_filled
        ]
        thread.slots_needed = still_needed

        if not still_needed:
            next_idx = (thread.workflow_step or 0) + 1
            if next_idx >= len(defn.steps):
                thread.status = ThreadStatus.RESOLVED
                return True
            thread.workflow_step = next_idx
            next_step = defn.steps[next_idx]
            thread.slots_needed = [
                s.name for s in next_step.slots_needed
                if s.required and s.name not in thread.slots_filled
            ]

        return False

    def get_instruction(self, thread: ConversationThread) -> str | None:
        """Generate system prompt instruction for the active workflow."""
        defn = self._definitions.get(thread.workflow_id or "")
        if defn is None or thread.status != ThreadStatus.ACTIVE:
            return None

        step = defn.steps[thread.workflow_step or 0]
        total = len(defn.steps)
        current = (thread.workflow_step or 0) + 1

        lines = [
            f'You are in the "{defn.name}" workflow, step {current}/{total}: "{step.description}".',
        ]
        if step.slots_needed:
            needed = [s for s in step.slots_needed if s.name not in thread.slots_filled]
            if needed:
                slot_desc = ", ".join(f"{s.name} ({s.description})" for s in needed)
                lines.append(f"You need to collect: {slot_desc}")
        if thread.slots_filled:
            filled = ", ".join(f"{k}={v}" for k, v in thread.slots_filled.items())
            lines.append(f"Already collected: {filled}")
        if step.tool_to_call:
            lines.append(
                f"Once all slots are filled, call the {step.tool_to_call} tool."
            )

        return "\n".join(lines)
