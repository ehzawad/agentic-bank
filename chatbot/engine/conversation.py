"""Core conversation engine — one turn at a time."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from chatbot.config import settings
from chatbot.engine.claude_client import ClaudeClient
from chatbot.engine.context_builder import build_system_prompt
from chatbot.guardrails.hallucination_blocker import HallucinationBlocker
from chatbot.guardrails.emotion_escalation import EmotionEscalation
from chatbot.memory.emotion_store import EmotionStore
from chatbot.memory.fact_store import FactStore
from chatbot.memory.session_store import SessionStore
from chatbot.memory.thread_store import ThreadStore
from chatbot.memory.turn_store import TurnStore
from chatbot.services.mock.auth import MockAuthService
from chatbot.state.machine import DialogueStateMachine
from chatbot.state.models import DialogueState
from chatbot.tools.definitions import TOOLS
from chatbot.tools.handlers import ToolHandlerRegistry
from chatbot.workflows.engine import WorkflowEngine
from chatbot.workflows.definitions.fraud_report import fraud_report
from chatbot.workflows.definitions.credit_card_application import credit_card_application
from chatbot.workflows.definitions.international_transfer import international_transfer

# Map tool names to the workflow they belong to
_TOOL_TO_WORKFLOW: dict[str, str] = {
    "block_card": "fraud_report",
    "file_dispute": "fraud_report",
    "order_replacement_card": "fraud_report",
    "initiate_transfer": "international_transfer",
}

# Map tool names to thread topic categories
_TOOL_TOPIC: dict[str, str] = {
    "get_balance": "account_inquiry",
    "get_transactions": "transaction_lookup",
    "block_card": "fraud_report",
    "order_replacement_card": "card_replacement",
    "get_card_details": "card_inquiry",
    "block_merchant": "merchant_block",
    "file_dispute": "dispute",
    "check_loan_eligibility": "loan_inquiry",
    "calculate_emi": "loan_inquiry",
    "check_mortgage_eligibility": "mortgage_inquiry",
    "get_exchange_rate": "transfer_inquiry",
    "initiate_transfer": "international_transfer",
    "generate_statement": "document_request",
    "get_tax_document": "document_request",
    "email_document": "document_request",
    "get_complaint_history": "complaint",
    "get_case_status": "complaint",
    "file_formal_complaint": "complaint",
    "initiate_human_transfer": "escalation",
    "search_knowledge_base": "faq",
}


@dataclass
class TurnResult:
    response: str
    state: str
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    emotion: str = "neutral"
    transferred_to_human: bool = False


class ConversationEngine:
    def __init__(
        self,
        session_id: str | None = None,
        tool_registry: ToolHandlerRegistry | None = None,
        auth_service: MockAuthService | None = None,
    ) -> None:
        self.session_store = SessionStore()
        self.fact_store = FactStore()
        self.thread_store = ThreadStore()
        self.emotion_store = EmotionStore()
        self.turn_store = TurnStore()
        self.state_machine = DialogueStateMachine()
        self.claude = ClaudeClient()
        self.tool_registry = tool_registry or ToolHandlerRegistry()
        self.auth_service = auth_service or MockAuthService()
        self.hallucination_blocker = HallucinationBlocker()
        self.emotion_escalation = EmotionEscalation()
        self.workflow_engine = WorkflowEngine()
        self.workflow_engine.register(fraud_report)
        self.workflow_engine.register(credit_card_application)
        self.workflow_engine.register(international_transfer)
        self._user_turn_counter: int = 0

        # Create session
        session = self.session_store.create(session_id)
        self._session_id = session.session_id

    @property
    def session_id(self) -> str:
        return self._session_id

    async def process_turn(self, user_message: str) -> TurnResult:
        """Process one user message and return the bot response."""

        # Step 1: State check — handle auth gate
        if self.state_machine.state == DialogueState.GREETING:
            self.state_machine.transition("user_message")
            return await self._handle_auth_greeting(user_message)

        if self.state_machine.requires_auth:
            return await self._handle_auth(user_message)

        if self.state_machine.state == DialogueState.HUMAN_TRANSFER:
            return TurnResult(
                response="You've been transferred to a human agent. They'll be with you shortly.",
                state=self.state_machine.state.value,
                transferred_to_human=True,
            )

        # Step 2: Append user message to turn store
        self.turn_store.append("user", user_message)
        self._user_turn_counter += 1

        # Step 3: Score emotion
        reading = self.emotion_store.score_turn(
            user_message, self._user_turn_counter
        )

        # Step 4: Check emotion escalation BEFORE calling Claude
        escalation = self.emotion_escalation.check(self.emotion_store.state)
        escalation_instruction = None
        if escalation.should_escalate:
            self.emotion_store.mark_escalation_triggered()
            escalation_instruction = escalation.instruction

        # Step 5: Build system prompt (with active workflow instruction if any)
        workflow_instruction = self._get_active_workflow_instruction()
        system_prompt = build_system_prompt(
            self.session_store,
            self.fact_store,
            self.thread_store,
            self.emotion_store,
            workflow_instruction=workflow_instruction,
        )
        if escalation_instruction:
            system_prompt += (
                f"\n\n<escalation_instruction>\n{escalation_instruction}\n"
                "Proactively offer to transfer the customer to a human agent.\n"
                "</escalation_instruction>"
            )

        # Step 6: Get messages and redact old tool results to prevent repetition
        messages = self.turn_store.get_messages()
        messages = _redact_old_tool_results(messages)
        tools = TOOLS if self.state_machine.tools_available else []

        response_text, updated_messages, tool_calls = await self.claude.run_tool_loop(
            system=system_prompt,
            messages=messages,
            tools=tools,
            tool_executor=self.tool_registry,
            fact_store=self.fact_store,
            turn_number=self._user_turn_counter,
        )

        # Step 7: Guardrails on final response
        g1_result = self.hallucination_blocker.scan(
            response_text, self.fact_store.get_current()
        )
        if not g1_result.safe:
            # Re-prompt Claude with stricter instruction
            reprompt_msg = (
                "Your previous response contained financial data not backed by tool results. "
                "Please regenerate your response using ONLY data from the tool results provided. "
                f"Ungrounded claims: {g1_result.ungrounded_claims}"
            )
            messages_copy = list(updated_messages)
            messages_copy.append({"role": "user", "content": reprompt_msg})
            response_text, _, extra_tools = await self.claude.run_tool_loop(
                system=system_prompt,
                messages=messages_copy,
                tools=tools,
                tool_executor=self.tool_registry,
                fact_store=self.fact_store,
                turn_number=self.turn_store.turn_number,
            )
            tool_calls.extend(extra_tools)

        # Step 8: Mark facts as presented and update turn store
        self.fact_store.mark_presented()
        self.turn_store.append("assistant", response_text)

        # Sync turn store messages with what Claude actually saw (tool loops)
        # The turn store keeps the simple view; updated_messages has the full history
        self._sync_messages(updated_messages)

        # Step 9: Track threads and manage workflows based on tool calls
        if tool_calls:
            tool_names = {tc["tool"] for tc in tool_calls}
            self._track_threads(tool_calls)

            if "initiate_human_transfer" in tool_names:
                self.state_machine.force_state(DialogueState.HUMAN_TRANSFER)
            elif "search_knowledge_base" in tool_names:
                self.state_machine.transition("faq_called")
                self.state_machine.transition("done")
            else:
                self.state_machine.transition("tool_called")
                self.state_machine.transition("done")

        # Detect farewell
        if _is_farewell(user_message, response_text):
            self.state_machine.transition("goodbye")

        return TurnResult(
            response=response_text,
            state=self.state_machine.state.value,
            tool_calls=tool_calls,
            emotion=reading.label,
            transferred_to_human=self.state_machine.state == DialogueState.HUMAN_TRANSFER,
        )

    async def _handle_auth_greeting(self, user_message: str) -> TurnResult:
        self.turn_store.append("user", user_message)
        system = (
            f"You are a customer service assistant for {settings.bank_name}. "
            "The customer just sent their first message. Respond naturally — "
            "match their tone (casual or formal). Then ask for their phone number "
            "or account number so you can verify their identity. "
            "Keep it to 1-2 short sentences. Do NOT repeat 'Welcome to HSBC' "
            "since the customer already saw a welcome message."
        )
        messages = [{"role": "user", "content": user_message}]
        response = await self.claude.create(system=system, messages=messages)
        greeting = response.content[0].text
        self.turn_store.append("assistant", greeting)
        self.state_machine.transition("identifier_provided")
        self.state_machine.force_state(DialogueState.AUTH_COLLECT)
        return TurnResult(response=greeting, state=self.state_machine.state.value)

    async def _handle_auth(self, user_message: str) -> TurnResult:
        self.turn_store.append("user", user_message)

        # Extract phone/account number from message
        identifier = _extract_identifier(user_message)
        if not identifier:
            resp = "I didn't catch that. Could you provide your phone number or account number?"
            self.turn_store.append("assistant", resp)
            return TurnResult(response=resp, state=self.state_machine.state.value)

        # Move to verify state, then attempt verification
        self.state_machine.transition("identifier_provided")

        result = await self.auth_service.verify(identifier)

        if result.get("verified"):
            session_data = {
                "customer_name": result.get("name"),
                "customer_id": result.get("customer_id"),
                "accounts": result.get("accounts", []),
                "cards": result.get("cards", []),
                "segment": result.get("segment"),
                "tenure": result.get("tenure"),
                "verified": True,
            }
            for key in ("credit_score_band", "vip_flag", "existing_mortgage"):
                if key in result:
                    session_data[key] = result[key]
            self.session_store.write(session_data)

            self.state_machine.transition("verified")
            name = result.get("name", "")
            system = (
                f"You are a customer service assistant for {settings.bank_name}. "
                f"You just verified the customer's identity — their name is {name}. "
                "Confirm verification naturally, matching the tone of the conversation so far. "
                "Keep it to 1-2 short sentences. Do NOT say 'Welcome to HSBC'."
            )
            messages = self.turn_store.get_messages()
            ver_resp = await self.claude.create(system=system, messages=messages)
            resp = ver_resp.content[0].text
            self.turn_store.append("assistant", resp)
            return TurnResult(response=resp, state=self.state_machine.state.value)
        else:
            session = self.session_store.session
            if session:
                session.auth_attempts += 1
                if session.auth_attempts >= settings.max_auth_attempts:
                    self.state_machine.transition("locked")
                    self.state_machine.transition("always")
                    resp = (
                        "I'm sorry, I wasn't able to verify your identity after "
                        "multiple attempts. Let me connect you with a team member "
                        "who can help."
                    )
                    self.turn_store.append("assistant", resp)
                    return TurnResult(
                        response=resp,
                        state=self.state_machine.state.value,
                        transferred_to_human=True,
                    )

            self.state_machine.transition("failed")
            resp = (
                "I wasn't able to verify that. Could you try again with your "
                "phone number or account number?"
            )
            self.turn_store.append("assistant", resp)
            return TurnResult(response=resp, state=self.state_machine.state.value)

    def _sync_messages(self, updated_messages: list[dict]) -> None:
        """Keep internal turn store aligned with actual conversation history.

        Preserves the user turn counter (which tracks actual user turns)
        separately from the message-level counter used by the turn store.
        """
        self.turn_store.clear()
        for msg in updated_messages:
            self.turn_store.append(msg["role"], msg["content"])

    def _track_threads(self, tool_calls: list[dict]) -> None:
        """Create or update conversation threads based on tools called."""
        for tc in tool_calls:
            tool_name = tc["tool"]
            topic = _TOOL_TOPIC.get(tool_name)
            if not topic:
                continue

            existing = self.thread_store.get_by_topic(topic)
            if existing is None:
                self._switch_to_topic(topic)
                self.thread_store.create(topic=topic)
            elif existing.status.value == "suspended":
                self._switch_to_topic(topic)
                self.thread_store.resume(existing.thread_id)

    def _switch_to_topic(self, topic: str) -> None:
        """Suspend active threads that don't match the given topic."""
        for active in self.thread_store.get_active():
            if active.topic != topic:
                self.thread_store.suspend(active.thread_id)

    def _get_active_workflow_instruction(self) -> str | None:
        """Get instruction for any active workflow thread."""
        for thread in self.thread_store.get_active():
            if thread.workflow_id:
                return self.workflow_engine.get_instruction(thread)
        return None


def _extract_identifier(text: str) -> str | None:
    """Extract phone number or account number from user text.

    Ignores dollar amounts and strips leading country code (+1).
    """
    # Remove dollar amounts so "$5000000" doesn't match as a phone
    cleaned = re.sub(r"\$[\d,]+\.?\d*", "", text)

    phone = re.findall(r"[\d\-\(\)\+\s]{7,}", cleaned)
    if phone:
        digits = "".join(c for c in phone[0] if c.isdigit())
        # Strip leading country code "1" if 11 digits (US numbers)
        if len(digits) == 11 and digits.startswith("1"):
            digits = digits[1:]
        if 7 <= len(digits) <= 10:
            return digits
    return None


def _redact_old_tool_results(messages: list[dict]) -> list[dict]:
    """Replace old tool_result content so Claude can't re-read raw data.

    Only redacts tool_result messages BEFORE the last plain user message
    (i.e., from previous turns, not the current turn's tool loop).
    """
    # Find the index of the last plain user message (the current turn)
    last_user_idx = -1
    for idx in range(len(messages) - 1, -1, -1):
        msg = messages[idx]
        if msg["role"] == "user" and isinstance(msg["content"], str):
            last_user_idx = idx
            break

    out: list[dict] = []
    for idx, msg in enumerate(messages):
        if idx >= last_user_idx:
            out.append(msg)
            continue

        # Redact tool_result messages from previous turns
        if msg["role"] == "user" and isinstance(msg["content"], list):
            has_tool_results = any(
                isinstance(b, dict) and b.get("type") == "tool_result"
                for b in msg["content"]
            )
            if has_tool_results:
                redacted = []
                for block in msg["content"]:
                    if isinstance(block, dict) and block.get("type") == "tool_result":
                        redacted.append({**block, "content": "(results delivered)"})
                    else:
                        redacted.append(block)
                out.append({"role": "user", "content": redacted})
                continue

        out.append(msg)
    return out


def _is_farewell(user_msg: str, bot_msg: str) -> bool:
    """Detect if the user is ending the conversation.

    Only triggers on short, standalone farewell messages.
    "thanks for the balance, now check my card" should NOT trigger.
    """
    lower = user_msg.lower().strip()
    words = lower.split()

    # Definite farewells regardless of length
    definite = {"bye", "goodbye", "bye bye"}
    if lower in definite:
        return True

    # Only count "thanks"/"thank you" as farewell if the message is short
    # (under 8 words) and doesn't contain continuation signals
    continuation_signals = {
        "but", "also", "and", "now", "another", "one more",
        "actually", "wait", "hold on", "before", "can you", "could you",
        "check", "show", "what", "how", "help",
    }
    if any(sig in lower for sig in continuation_signals):
        return False

    short_farewells = {"thanks", "thank you", "that's all", "that's everything", "that's it", "all good"}
    if len(words) <= 8 and any(f in lower for f in short_farewells):
        return True

    return False
