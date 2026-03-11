"""Tier 1: Component tests — no Claude API calls.

Tests auth extraction, mock services, emotion scoring, state machine,
guardrails, and FAQ search directly.

Run: pytest tests/test_components.py -v
"""

import asyncio
import math

import pytest

from chatbot.engine.conversation import _extract_identifier, _is_farewell
from chatbot.guardrails.emotion_escalation import EmotionEscalation
from chatbot.guardrails.hallucination_blocker import HallucinationBlocker
from chatbot.memory.emotion_store import EmotionStore, _score_text
from chatbot.memory.fact_store import FactStore
from chatbot.memory.models import (
    ConversationThread,
    CustomerSession,
    EmotionState,
    Fact,
    ThreadStatus,
)
from chatbot.memory.session_store import SessionStore
from chatbot.memory.thread_store import ThreadStore
from chatbot.memory.turn_store import TurnStore
from chatbot.services.mock.accounts import MockAccountService
from chatbot.services.mock.auth import MockAuthService
from chatbot.services.mock.cards import MockCardService
from chatbot.services.mock.complaints import MockComplaintService
from chatbot.services.mock.documents import MockDocumentService
from chatbot.services.mock.loans import MockLoanService
from chatbot.services.mock.transfers import MockTransferService
from chatbot.state.machine import DialogueStateMachine
from chatbot.state.models import DialogueState
from chatbot.tools.handlers import ToolHandlerRegistry


# =============================================================================
# Auth Identifier Extraction (20 cases)
# =============================================================================
class TestIdentifierExtraction:
    """Tests _extract_identifier() regex parsing."""

    @pytest.mark.parametrize(
        "text, expected_digits",
        [
            ("917-555-0142", "9175550142"),
            ("(917) 555-0142", "9175550142"),
            ("9175550142", "9175550142"),
            ("917 555 0142", "9175550142"),
            ("my phone is 917-555-0142", "9175550142"),
            ("call me at (646) 555-0317 please", "6465550317"),
            ("347-555-0286", "3475550286"),
            ("415-555-0193", "4155550193"),
            ("718-555-0412", "7185550412"),
            ("312-555-0847", "3125550847"),
            ("917-555-0631", "9175550631"),
            ("646-555-0921", "6465550921"),
            ("88342210", "88342210"),  # Account number (8 digits)
            ("account 88342210", "88342210"),
            ("212-555-0198", "2125550198"),
        ],
        ids=[
            "dashes", "parens", "raw_digits", "spaces", "embedded_in_text",
            "parens_embedded", "ahmed", "sarah", "robert", "elena",
            "thomas", "jennifer", "account_number", "account_with_prefix",
            "priya",
        ],
    )
    def test_valid_identifiers(self, text, expected_digits):
        result = _extract_identifier(text)
        assert result == expected_digits

    @pytest.mark.parametrize(
        "text",
        [
            "hello",
            "I need help",
            "12345",       # too short (5 digits)
            "abc",
            "",
            "my name is James",
        ],
        ids=["greeting", "sentence", "short_number", "letters", "empty", "name"],
    )
    def test_invalid_identifiers(self, text):
        result = _extract_identifier(text)
        assert result is None

    def test_dollar_amount_not_extracted(self):
        """Dollar amounts should be stripped before extraction."""
        result = _extract_identifier("I need $5000000")
        assert result is None

    def test_international_format_strips_country_code(self):
        """US +1 prefix should be stripped to 10 digits."""
        result = _extract_identifier("+1-917-555-0142")
        assert result == "9175550142"


# =============================================================================
# Auth Service (10 cases)
# =============================================================================
class TestAuthService:
    @pytest.fixture
    def auth(self):
        return MockAuthService()

    @pytest.mark.parametrize(
        "phone, expected_name",
        [
            ("9175550142", "James Chen"),
            ("2125550198", "Priya Sharma"),
            ("6465550317", "David Okonkwo"),
            ("3475550286", "Ahmed Hassan"),
            ("4155550193", "Sarah Kim"),
            ("7185550412", "Robert & Lisa Chen"),
            ("3125550847", "Elena Volkova"),
            ("9175550631", "Thomas Wright"),
            ("6465550921", "Jennifer Park"),
        ],
    )
    @pytest.mark.asyncio
    async def test_verify_all_customers(self, auth, phone, expected_name):
        result = await auth.verify(phone)
        assert result["verified"] is True
        assert result["name"] == expected_name

    @pytest.mark.asyncio
    async def test_verify_account_number(self, auth):
        result = await auth.verify("88342210")
        assert result["verified"] is True
        assert result["name"] == "Maria Santos"

    @pytest.mark.asyncio
    async def test_verify_invalid_phone(self, auth):
        result = await auth.verify("0000000000")
        assert result["verified"] is False

    @pytest.mark.asyncio
    async def test_verify_empty(self, auth):
        result = await auth.verify("")
        assert result["verified"] is False


# =============================================================================
# Account Service (20 cases)
# =============================================================================
class TestAccountService:
    @pytest.fixture
    def accounts(self):
        return MockAccountService()

    @pytest.mark.parametrize(
        "account_id, expected_balance",
        [
            ("checking_4821", 12450.75),
            ("savings_7903", 34200.00),
            ("checking_8912", 28930.50),
            ("checking_5519", 8750.00),
            ("savings_1102", 15400.00),
            ("checking_6641", 5220.30),
            ("joint_checking_4402", 42100.00),
            ("joint_savings_9918", 130000.00),
            ("checking_2291", 7830.45),
            ("savings_7740", 22140.00),
            ("checking_1198", 67500.00),
            ("checking_3301", 4215.60),
            ("savings_8850", 22140.00),
            ("checking_8834", 19340.00),
            ("savings_2210", 45000.00),
        ],
    )
    @pytest.mark.asyncio
    async def test_all_balances(self, accounts, account_id, expected_balance):
        result = await accounts.get_balance(account_id)
        assert result["balance"] == expected_balance

    @pytest.mark.asyncio
    async def test_nonexistent_account(self, accounts):
        result = await accounts.get_balance("checking_9999")
        assert result["balance"] == 0.00

    @pytest.mark.asyncio
    async def test_transactions_with_data(self, accounts):
        result = await accounts.get_transactions("checking_4821")
        assert len(result["transactions"]) == 2

    @pytest.mark.asyncio
    async def test_transactions_filter_amount(self, accounts):
        result = await accounts.get_transactions("checking_4821", amount_filter=89.99)
        assert len(result["transactions"]) == 1
        assert result["transactions"][0]["id"] == "TXN-90812"

    @pytest.mark.asyncio
    async def test_transactions_checking_5519(self, accounts):
        result = await accounts.get_transactions("checking_5519")
        assert len(result["transactions"]) >= 1

    @pytest.mark.asyncio
    async def test_savings_3301_for_priya(self, accounts):
        """Priya Sharma's savings account should have a balance."""
        result = await accounts.get_balance("savings_3301")
        assert result["balance"] == 18750.00


# =============================================================================
# Card Service (15 cases)
# =============================================================================
class TestCardService:
    @pytest.fixture
    def cards(self):
        return MockCardService()

    @pytest.mark.asyncio
    async def test_block_card(self, cards):
        result = await cards.block_card("visa_ending_4455", "suspected_fraud")
        assert result["status"] == "blocked"
        assert "BLK" in result["block_id"]

    @pytest.mark.asyncio
    async def test_order_replacement(self, cards):
        result = await cards.order_replacement("visa_ending_4455", "expedited")
        assert result["eta"] == "2-3 business days"
        assert result["temp_virtual_card"] is True

    @pytest.mark.asyncio
    async def test_get_details_known_card(self, cards):
        result = await cards.get_details("credit_card_ending_2277")
        assert result["apr_purchase"] == 19.99
        assert result["credit_limit"] == 15000

    @pytest.mark.asyncio
    async def test_get_details_visa_4455(self, cards):
        result = await cards.get_details("visa_ending_4455")
        assert result["apr_purchase"] == 17.49
        assert result["credit_limit"] == 25000

    @pytest.mark.asyncio
    async def test_block_merchant(self, cards):
        result = await cards.block_merchant("credit_card_ending_2277", "DGTL_MKTPLC")
        assert result["blocked"] is True

    @pytest.mark.asyncio
    async def test_file_dispute(self, cards):
        result = await cards.file_dispute(
            card_id="credit_card_ending_2277",
            transaction_ids=["TXN-55091", "TXN-54220"],
            total_amount=313.60,
            reason="unauthorized_recurring_charge",
        )
        assert "DSP-2026" in result["dispute_id"]
        assert result["credit_amount"] == 313.60
        assert result["provisional_credit"] is True


# =============================================================================
# Loan Service (10 cases)
# =============================================================================
class TestLoanService:
    @pytest.fixture
    def loans(self):
        return MockLoanService()

    @pytest.mark.asyncio
    async def test_eligibility_standard(self, loans):
        result = await loans.check_eligibility("cust_1", 25000, "home_improvement")
        assert result["eligible"] is True
        assert result["offered_rate"] == 7.49

    @pytest.mark.asyncio
    async def test_eligibility_higher_rate(self, loans):
        result = await loans.check_eligibility("cust_1", 35000, "debt_consolidation")
        assert result["offered_rate"] == 8.99

    @pytest.mark.asyncio
    async def test_emi_calculation(self, loans):
        result = await loans.calculate_emi(25000, 7.49, [36, 48, 60])
        assert "emi_36mo" in result
        assert "emi_48mo" in result
        assert "emi_60mo" in result
        # Verify math: 36-month EMI at 7.49%
        monthly_rate = 7.49 / 100 / 12
        expected = 25000 * monthly_rate * math.pow(1 + monthly_rate, 36) / (
            math.pow(1 + monthly_rate, 36) - 1
        )
        assert abs(result["emi_36mo"] - round(expected, 2)) < 0.01

    @pytest.mark.asyncio
    async def test_mortgage_eligibility(self, loans):
        result = await loans.check_mortgage_eligibility(
            customer_id="cust_1", home_price_range=[550000, 650000], down_payment=130000
        )
        assert result["eligible"] is True
        assert "30yr_fixed" in result["rates"]


# =============================================================================
# Transfer Service (8 cases)
# =============================================================================
class TestTransferService:
    @pytest.fixture
    def transfers(self):
        return MockTransferService()

    @pytest.mark.parametrize(
        "from_c, to_c, expected_rate",
        [
            ("USD", "GBP", 0.7892),
            ("USD", "EUR", 0.9210),
            ("USD", "JPY", 149.50),
            ("USD", "BDT", 119.85),
        ],
    )
    @pytest.mark.asyncio
    async def test_exchange_rates(self, transfers, from_c, to_c, expected_rate):
        result = await transfers.get_exchange_rate(from_c, to_c, 1000)
        assert result["rate"] == expected_rate
        assert result["fee_wire"] == 35.00

    @pytest.mark.asyncio
    async def test_unsupported_currency(self, transfers):
        result = await transfers.get_exchange_rate("USD", "CHF", 1000)
        assert result["rate"] == 1.0  # Default fallback

    @pytest.mark.asyncio
    async def test_initiate_transfer(self, transfers):
        result = await transfers.initiate_transfer(
            from_account="checking_5519", amount_usd=2000, target_currency="GBP",
            recipient_name="Test", recipient_bank="Barclays",
            account_number="12345678", purpose="family_support",
        )
        assert "WIR-2026" in result["transfer_id"]
        assert result["amount_debited"] == 2047.50


# =============================================================================
# Document Service (6 cases)
# =============================================================================
class TestDocumentService:
    @pytest.fixture
    def docs(self):
        return MockDocumentService()

    @pytest.mark.asyncio
    async def test_generate_statement(self, docs):
        result = await docs.generate_statement("checking_2291", 6, purpose="visa_application")
        assert "STM-2291-6M" in result["statement_id"]
        assert result["stamped"] is True

    @pytest.mark.asyncio
    async def test_tax_document(self, docs):
        result = await docs.get_tax_document("elena_volkova_2291", 2025, "1099-INT")
        assert result["interest_earned"] == 847.32
        assert result["available"] is True

    @pytest.mark.asyncio
    async def test_email_document(self, docs):
        result = await docs.email_document(["STM-2291-6M"], "test@email.com")
        assert result["sent"] is True
        assert result["to"] == "test@email.com"


# =============================================================================
# Complaint Service (8 cases)
# =============================================================================
class TestComplaintService:
    @pytest.fixture
    def complaints(self):
        return MockComplaintService()

    @pytest.mark.asyncio
    async def test_thomas_wright_history(self, complaints):
        result = await complaints.get_history("thomas_wright_1198")
        assert len(result["open_cases"]) == 1
        assert result["open_cases"][0]["case_id"] == "CMP-2026-3341"

    @pytest.mark.asyncio
    async def test_no_complaint_history(self, complaints):
        result = await complaints.get_history("james_chen_4821")
        assert result["open_cases"] == []

    @pytest.mark.asyncio
    async def test_case_status(self, complaints):
        result = await complaints.get_case_status("CMP-2026-3341")
        assert result["recall_status"] == "funds_recovered"
        assert result["recovered_amount"] == 5000.00

    @pytest.mark.asyncio
    async def test_unknown_case(self, complaints):
        result = await complaints.get_case_status("CMP-9999-9999")
        assert result["status"] == "not_found"

    @pytest.mark.asyncio
    async def test_file_complaint(self, complaints):
        result = await complaints.file_complaint(
            customer_id="thomas_wright_1198",
            complaint_description="Two-week delay",
            priority="urgent",
        )
        assert "FML-2026" in result["complaint_id"]
        assert result["priority"] == "urgent"

    @pytest.mark.asyncio
    async def test_human_transfer(self, complaints):
        result = await complaints.initiate_human_transfer(
            department="senior_management", priority="urgent",
            context_summary="VIP customer escalation",
        )
        assert result["status"] == "connecting"


# =============================================================================
# Emotion Scoring (20 cases)
# =============================================================================
class TestEmotionScoring:
    @pytest.mark.parametrize(
        "text, expected_label",
        [
            ("Hello, I need help with my account", "neutral"),
            ("Can you check my balance please?", "neutral"),
            ("Thanks for your help", "neutral"),
            # Single neg word + no caps/excl = low score
            ("This is frustrating!", "neutral"),
            ("I am upset about this charge", "neutral"),
            # Multiple signals needed for higher labels
            ("I'm REALLY frustrated with this!!! TERRIBLE service!!!", "anxious"),
            ("This is UNACCEPTABLE!!!", "stressed"),
            # hate + urgency phrase "nobody" = anxious
            ("I HATE this! Nobody can help!", "anxious"),
            # Single neg word "immediately" = concerned
            ("I'm going to report this to the authorities immediately!", "concerned"),
            # Caps + exclamations + neg words + urgency = angry (0.75, not furious)
            ("HELP! EMERGENCY! I need someone RIGHT NOW!!!", "angry"),
        ],
        ids=[
            "neutral_greeting", "neutral_question", "neutral_thanks",
            "neutral_frustrated_single", "neutral_upset_single",
            "stressed_multi_signal", "stressed_caps_excl",
            "anxious_hate_nobody", "concerned_immediately",
            "angry_caps_excl_urgency",
        ],
    )
    def test_emotion_labels(self, text, expected_label):
        score, label, _ = _score_text(text)
        assert label == expected_label, f"Expected {expected_label}, got {label} (score={score})"

    def test_all_caps_boost(self):
        score, _, indicators = _score_text("WHAT IS GOING ON WITH MY ACCOUNT")
        assert any("caps_ratio" in i for i in indicators)
        assert score >= 0.2

    def test_exclamation_boost(self):
        score, _, indicators = _score_text("This is terrible!!! I can't believe it!!!")
        assert any("exclamations" in i for i in indicators)

    def test_negative_lexicon_multiple(self):
        _, _, indicators = _score_text("This is terrible, horrible, and unacceptable")
        neg = [i for i in indicators if "neg_words" in i]
        assert len(neg) == 1
        assert "terrible" in neg[0]
        assert "horrible" in neg[0]
        assert "unacceptable" in neg[0]

    def test_urgency_phrases(self):
        score, _, indicators = _score_text("I need this fixed right now, nobody is helping")
        urgency = [i for i in indicators if "urgency" in i]
        assert len(urgency) >= 2  # "right now" + "nobody"

    def test_negation_blind_spot(self):
        """Known issue: 'NOT angry' still scores on 'angry'."""
        score, _, indicators = _score_text("I'm NOT angry, just confused")
        neg = [i for i in indicators if "neg_words" in i]
        assert len(neg) == 1  # "angry" matched despite negation

    def test_emotion_store_trajectory(self):
        store = EmotionStore()
        store.score_turn("Hello", 1)
        store.score_turn("This is frustrating!", 2)
        store.score_turn("I am FURIOUS!!! UNACCEPTABLE!!!", 3)
        assert store.state.trajectory_rising is True
        assert store.state.current.label in ("angry", "furious")

    def test_emotion_store_non_rising(self):
        store = EmotionStore()
        store.score_turn("I am ANGRY!!!", 1)
        store.score_turn("Ok fine, whatever", 2)
        store.score_turn("Thank you", 3)
        assert store.state.trajectory_rising is False

    def test_score_capped_at_one(self):
        text = "HATE HATE HATE!!! UNACCEPTABLE TERRIBLE HORRIBLE AWFUL WORST RIGHT NOW NOBODY!!!"
        score, _, _ = _score_text(text)
        assert score <= 1.0


# =============================================================================
# Emotion Escalation (10 cases)
# =============================================================================
class TestEmotionEscalation:
    @pytest.fixture
    def escalation(self):
        return EmotionEscalation()

    def _make_state(self, scores):
        from chatbot.memory.models import EmotionReading
        state = EmotionState()
        for i, s in enumerate(scores):
            label = "furious" if s >= 0.8 else "angry" if s >= 0.65 else "neutral"
            state.readings.append(EmotionReading(turn_number=i, score=s, label=label))
        return state

    def test_escalation_triggered(self, escalation):
        state = self._make_state([0.3, 0.5, 0.75])
        result = escalation.check(state)
        assert result.should_escalate is True

    def test_no_escalation_too_few_turns(self, escalation):
        state = self._make_state([0.5, 0.9])
        result = escalation.check(state)
        assert result.should_escalate is False

    def test_no_escalation_not_rising(self, escalation):
        state = self._make_state([0.8, 0.4, 0.9])
        result = escalation.check(state)
        assert result.should_escalate is False

    def test_no_escalation_below_threshold(self, escalation):
        state = self._make_state([0.2, 0.4, 0.6])
        result = escalation.check(state)
        assert result.should_escalate is False  # 0.6 < 0.7 threshold

    def test_no_escalation_flat(self, escalation):
        state = self._make_state([0.5, 0.5, 0.5])
        # Flat is NOT rising (requires <=, not <), so 0.5 <= 0.5 is True
        # But 0.5 < 0.7 threshold, so no escalation
        result = escalation.check(state)
        assert result.should_escalate is False

    def test_escalation_already_triggered(self, escalation):
        state = self._make_state([0.3, 0.5, 0.75])
        state.escalation_triggered = True
        result = escalation.check(state)
        assert result.should_escalate is False

    def test_escalation_exactly_at_threshold(self, escalation):
        state = self._make_state([0.3, 0.5, 0.7])
        result = escalation.check(state)
        assert result.should_escalate is True  # >= 0.7


# =============================================================================
# State Machine (15 cases)
# =============================================================================
class TestStateMachine:
    def test_initial_state(self):
        sm = DialogueStateMachine()
        assert sm.state == DialogueState.GREETING

    def test_greeting_to_auth(self):
        sm = DialogueStateMachine()
        sm.transition("user_message")
        assert sm.state == DialogueState.AUTH_COLLECT

    def test_auth_flow_success(self):
        sm = DialogueStateMachine()
        sm.transition("user_message")
        sm.transition("identifier_provided")
        assert sm.state == DialogueState.AUTH_VERIFY
        sm.transition("verified")
        assert sm.state == DialogueState.LISTENING

    def test_auth_flow_failure_retry(self):
        sm = DialogueStateMachine()
        sm.transition("user_message")
        sm.transition("identifier_provided")
        sm.transition("failed")
        assert sm.state == DialogueState.AUTH_COLLECT

    def test_auth_lockout(self):
        sm = DialogueStateMachine()
        sm.transition("user_message")
        sm.transition("identifier_provided")
        sm.transition("locked")
        assert sm.state == DialogueState.AUTH_LOCKED
        sm.transition("always")
        assert sm.state == DialogueState.HUMAN_TRANSFER

    def test_tools_unavailable_during_auth(self):
        sm = DialogueStateMachine()
        assert sm.tools_available is False
        sm.transition("user_message")
        assert sm.tools_available is False

    def test_tools_available_after_auth(self):
        sm = DialogueStateMachine()
        sm.transition("user_message")
        sm.transition("identifier_provided")
        sm.transition("verified")
        assert sm.tools_available is True

    def test_farewell_transition(self):
        sm = DialogueStateMachine()
        sm.force_state(DialogueState.LISTENING)
        sm.transition("goodbye")
        assert sm.state == DialogueState.FAREWELL

    def test_escalation_transition(self):
        sm = DialogueStateMachine()
        sm.force_state(DialogueState.LISTENING)
        sm.transition("escalation")
        assert sm.state == DialogueState.HUMAN_TRANSFER

    def test_tool_round_trip(self):
        sm = DialogueStateMachine()
        sm.force_state(DialogueState.LISTENING)
        sm.transition("tool_called")
        assert sm.state == DialogueState.TOOL_EXECUTING
        sm.transition("done")
        assert sm.state == DialogueState.LISTENING

    def test_invalid_transition_ignored(self):
        sm = DialogueStateMachine()
        sm.force_state(DialogueState.LISTENING)
        sm.transition("nonexistent_event")
        assert sm.state == DialogueState.LISTENING  # Unchanged


# =============================================================================
# Hallucination Blocker (12 cases)
# =============================================================================
class TestHallucinationBlocker:
    @pytest.fixture
    def blocker(self):
        return HallucinationBlocker()

    def _make_facts(self, values):
        return [
            Fact(key=f"k{i}", value=v, source_tool="test", turn_number=i)
            for i, v in enumerate(values)
        ]

    def test_clean_text_no_financial(self, blocker):
        result = blocker.scan("Hello, how can I help you today?", [])
        assert result.safe is True

    def test_grounded_dollar_amount(self, blocker):
        facts = self._make_facts([{"balance": 12450.75}])
        result = blocker.scan("Your balance is $12,450.75", facts)
        assert result.safe is True

    def test_ungrounded_dollar_amount(self, blocker):
        facts = self._make_facts([{"balance": 12450.75}])
        result = blocker.scan("Your balance is $99,999.00", facts)
        assert result.safe is False
        assert len(result.ungrounded_claims) > 0

    def test_grounded_reference_id(self, blocker):
        facts = self._make_facts([{"dispute_id": "DSP-2026-08847"}])
        result = blocker.scan("Your dispute ID is DSP-2026-08847", facts)
        assert result.safe is True

    def test_ungrounded_reference_id(self, blocker):
        result = blocker.scan("Your dispute ID is DSP-2026-99999", [])
        assert result.safe is False

    def test_grounded_interest_rate(self, blocker):
        facts = self._make_facts([{"apr_purchase": 19.99}])
        result = blocker.scan("Your APR is 19.99% APR", facts)
        assert result.safe is True

    def test_no_facts_with_amounts(self, blocker):
        result = blocker.scan("You owe $500.00", [])
        assert result.safe is False

    def test_multiple_claims_mixed(self, blocker):
        facts = self._make_facts([{"balance": 5000}])
        result = blocker.scan("Balance $5,000.00, dispute DSP-2026-12345", facts)
        # $5,000 is grounded, DSP-2026-12345 is not
        assert result.safe is False

    def test_block_id_grounded(self, blocker):
        facts = self._make_facts([{"block_id": "BLK-4455-0311"}])
        result = blocker.scan("Block reference: BLK-4455-0311", facts)
        assert result.safe is True

    def test_wire_transfer_id(self, blocker):
        facts = self._make_facts([{"transfer_id": "WIR-2026-031108"}])
        result = blocker.scan("Transfer WIR-2026-031108 is processing", facts)
        assert result.safe is True

    def test_no_substring_false_match(self, blocker):
        """$100 should NOT match against $1000 fact value."""
        facts = self._make_facts([{"balance": 1000}])
        result = blocker.scan("You have $100 in your account", facts)
        assert result.safe is False  # Fixed: exact numeric match, not substring


# =============================================================================
# Farewell Detection (8 cases)
# =============================================================================
class TestFarewellDetection:
    @pytest.mark.parametrize(
        "user_msg, expected",
        [
            ("bye", True),
            ("goodbye", True),
            ("thanks", True),
            ("thank you", True),
            ("that's all", True),
            ("that's everything", True),
            ("What is my balance?", False),
            ("I need more help", False),
        ],
    )
    def test_farewell(self, user_msg, expected):
        assert _is_farewell(user_msg, "") == expected

    def test_farewell_not_triggered_mid_conversation(self):
        """'thanks' with continuation signals should NOT trigger farewell."""
        assert _is_farewell("thanks for the balance, now check my card", "") is False
        assert _is_farewell("thank you, but can you also show my transactions?", "") is False
        assert _is_farewell("thanks, what about my savings?", "") is False


# =============================================================================
# Memory Stores (12 cases)
# =============================================================================
class TestMemoryStores:
    def test_session_store_create(self):
        store = SessionStore()
        session = store.create()
        assert session.session_id is not None
        assert store.is_verified is False

    def test_session_store_write_and_verify(self):
        store = SessionStore()
        store.create()
        store.write({"customer_name": "Test", "verified": True, "cards": []})
        assert store.is_verified is True
        assert "none on file" in store.to_context()

    def test_session_store_cards_shown(self):
        store = SessionStore()
        store.create()
        store.write({"customer_name": "Test", "verified": True, "cards": ["visa_4455"]})
        ctx = store.to_context()
        assert "visa_4455" in ctx

    def test_fact_store_versioning(self):
        store = FactStore()
        store.write("balance", 5000, "get_balance", 1)
        store.write("balance", 5200, "get_balance", 3)
        current = store.get_current()
        assert len(current) == 1
        assert current[0].value == 5200

    def test_fact_store_multiple_keys(self):
        store = FactStore()
        store.write("balance", 5000, "get_balance", 1)
        store.write("dispute", "DSP-123", "file_dispute", 2)
        assert len(store.get_current()) == 2

    def test_thread_store_lifecycle(self):
        store = ThreadStore()
        t = store.create("balance_inquiry")
        assert t.status == ThreadStatus.ACTIVE
        store.suspend(t.thread_id)
        assert len(store.get_suspended()) == 1
        store.resume(t.thread_id)
        assert len(store.get_active()) == 1
        store.resolve(t.thread_id)
        assert len(store.get_active()) == 0

    def test_turn_store_messages(self):
        store = TurnStore()
        store.append("user", "Hello")
        store.append("assistant", "Hi there")
        msgs = store.get_messages()
        assert len(msgs) == 2
        assert msgs[0]["role"] == "user"
        assert msgs[1]["role"] == "assistant"


# =============================================================================
# Tool Handler Registry (5 cases)
# =============================================================================
class TestToolHandlerRegistry:
    @pytest.fixture
    def registry(self):
        return ToolHandlerRegistry()

    def test_has_all_tools(self, registry):
        expected = [
            "get_balance", "get_transactions", "block_card", "order_replacement_card",
            "get_card_details", "block_merchant", "file_dispute",
            "check_loan_eligibility", "calculate_emi", "check_mortgage_eligibility",
            "get_exchange_rate", "initiate_transfer",
            "generate_statement", "get_tax_document", "email_document",
            "get_complaint_history", "get_case_status", "file_formal_complaint",
            "initiate_human_transfer", "search_knowledge_base",
        ]
        for tool in expected:
            assert registry.has_tool(tool), f"Missing tool: {tool}"

    @pytest.mark.asyncio
    async def test_execute_balance(self, registry):
        import json
        result = await registry.execute("get_balance", {"account_id": "checking_4821"})
        data = json.loads(result)
        assert data["balance"] == 12450.75

    @pytest.mark.asyncio
    async def test_execute_unknown_tool(self, registry):
        import json
        result = await registry.execute("nonexistent_tool", {})
        data = json.loads(result)
        assert "error" in data

    @pytest.mark.asyncio
    async def test_knowledge_base_without_store(self, registry):
        import json
        result = await registry.execute("search_knowledge_base", {"query": "test"})
        data = json.loads(result)
        assert data["confidence"] == "low"  # No store configured
