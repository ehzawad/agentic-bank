from enum import Enum


class DialogueState(str, Enum):
    GREETING = "greeting"
    AUTH_COLLECT = "auth_collect"
    AUTH_VERIFY = "auth_verify"
    AUTH_LOCKED = "auth_locked"
    LISTENING = "listening"
    TOOL_EXECUTING = "tool_executing"
    FAQ_SEARCHING = "faq_searching"
    WORKFLOW_ACTIVE = "workflow_active"
    WORKFLOW_SUSPENDED = "workflow_suspended"
    HUMAN_TRANSFER = "human_transfer"
    FAREWELL = "farewell"
