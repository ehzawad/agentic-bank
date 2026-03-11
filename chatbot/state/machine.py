from __future__ import annotations

from chatbot.state.models import DialogueState


class DialogueStateMachine:
    def __init__(self) -> None:
        self._state = DialogueState.GREETING

    @property
    def state(self) -> DialogueState:
        return self._state

    @property
    def requires_auth(self) -> bool:
        return self._state in (
            DialogueState.GREETING,
            DialogueState.AUTH_COLLECT,
            DialogueState.AUTH_VERIFY,
            DialogueState.AUTH_LOCKED,
        )

    @property
    def tools_available(self) -> bool:
        return not self.requires_auth and self._state != DialogueState.HUMAN_TRANSFER

    def transition(self, event: str) -> DialogueState:
        transitions: dict[DialogueState, dict[str, DialogueState]] = {
            DialogueState.GREETING: {
                "user_message": DialogueState.AUTH_COLLECT,
            },
            DialogueState.AUTH_COLLECT: {
                "identifier_provided": DialogueState.AUTH_VERIFY,
            },
            DialogueState.AUTH_VERIFY: {
                "verified": DialogueState.LISTENING,
                "failed": DialogueState.AUTH_COLLECT,
                "locked": DialogueState.AUTH_LOCKED,
            },
            DialogueState.AUTH_LOCKED: {
                "always": DialogueState.HUMAN_TRANSFER,
            },
            DialogueState.LISTENING: {
                "tool_called": DialogueState.TOOL_EXECUTING,
                "faq_called": DialogueState.FAQ_SEARCHING,
                "workflow_started": DialogueState.WORKFLOW_ACTIVE,
                "escalation": DialogueState.HUMAN_TRANSFER,
                "goodbye": DialogueState.FAREWELL,
            },
            DialogueState.TOOL_EXECUTING: {
                "done": DialogueState.LISTENING,
            },
            DialogueState.FAQ_SEARCHING: {
                "done": DialogueState.LISTENING,
            },
            DialogueState.WORKFLOW_ACTIVE: {
                "step_done": DialogueState.WORKFLOW_ACTIVE,
                "workflow_done": DialogueState.LISTENING,
                "topic_switch": DialogueState.WORKFLOW_SUSPENDED,
                "escalation": DialogueState.HUMAN_TRANSFER,
                "goodbye": DialogueState.FAREWELL,
            },
            DialogueState.WORKFLOW_SUSPENDED: {
                "resumed": DialogueState.WORKFLOW_ACTIVE,
                "expired": DialogueState.LISTENING,
            },
        }

        state_transitions = transitions.get(self._state, {})
        new_state = state_transitions.get(event)
        if new_state is not None:
            self._state = new_state
        return self._state

    def force_state(self, state: DialogueState) -> None:
        self._state = state
