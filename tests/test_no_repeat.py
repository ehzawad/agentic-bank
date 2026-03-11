"""Test that the chatbot doesn't repeat already-communicated facts.

Reproduces the exact bug: user asks about a charge, gets told about it,
then asks about balance — bot should NOT re-state the charge info.
Then user says "maybe I am not sure" — bot should NOT re-state balance or charges.
"""

import asyncio
import json
from unittest.mock import AsyncMock, patch

from chatbot.engine.conversation import ConversationEngine
from chatbot.engine.context_builder import build_system_prompt
from chatbot.memory.fact_store import FactStore
from chatbot.memory.emotion_store import EmotionStore
from chatbot.memory.session_store import SessionStore
from chatbot.memory.thread_store import ThreadStore


# ---------------------------------------------------------------------------
# Unit test: FactStore annotation logic
# ---------------------------------------------------------------------------

def test_fact_store_marks_presented():
    """After mark_presented(), facts show as ALREADY COMMUNICATED."""
    fs = FactStore()
    fs.write("balance", 3841.20, "get_balance", turn_number=1)
    fs.write("txn_1", {"merchant": "DGTL MKTPLC"}, "get_transactions", turn_number=1)

    ctx_before = fs.to_context()
    assert "[NEW" in ctx_before
    assert "ALREADY COMMUNICATED" not in ctx_before

    fs.mark_presented()

    ctx_after = fs.to_context()
    assert "ALREADY COMMUNICATED" in ctx_after
    assert "[NEW" not in ctx_after


def test_new_facts_stay_new_old_stay_old():
    """After mark + new fact, context has both sections."""
    fs = FactStore()
    fs.write("balance", 3841.20, "get_balance", turn_number=1)
    fs.mark_presented()

    fs.write("card_details", {"card": "2277"}, "get_card_details", turn_number=2)

    ctx = fs.to_context()
    assert "[NEW" in ctx
    assert "ALREADY COMMUNICATED" in ctx
    # New fact should be in the NEW section
    assert "card_details" in ctx.split("ALREADY COMMUNICATED")[0]
    # Old fact should be in the ALREADY COMMUNICATED section
    assert "get_balance" in ctx.split("ALREADY COMMUNICATED")[1]


def test_system_prompt_contains_annotations():
    """build_system_prompt includes the annotated fact sections."""
    ss = SessionStore()
    ss.create()
    fs = FactStore()
    ts = ThreadStore()
    es = EmotionStore()

    fs.write("balance", 3841.20, "get_balance", turn_number=1)
    fs.mark_presented()
    fs.write("txn", {"m": "DGTL"}, "get_transactions", turn_number=2)

    prompt = build_system_prompt(ss, fs, ts, es)
    assert "ALREADY COMMUNICATED" in prompt
    assert "[NEW" in prompt


# ---------------------------------------------------------------------------
# Integration test: full conversation flow with mocked Claude
# ---------------------------------------------------------------------------

def test_conversation_marks_facts_after_response():
    """After process_turn, facts from that turn are marked as presented,
    so the NEXT turn's system prompt shows them as ALREADY COMMUNICATED."""

    captured_system_prompts: list[str] = []

    async def mock_run_tool_loop(system, messages, tools, tool_executor,
                                  fact_store=None, turn_number=0):
        captured_system_prompts.append(system)

        # Simulate Claude calling get_card_details + get_transactions on turn 1
        if turn_number == 1:
            # Simulate tool writing facts (normally done inside run_tool_loop)
            if fact_store:
                fact_store.write(
                    "get_card_details_abc123",
                    {"card_id": "credit_card_ending_2277", "balance": 3841.20},
                    "get_card_details",
                    turn_number,
                )
                fact_store.write(
                    "get_transactions_def456",
                    {"transactions": [
                        {"merchant": "DGTL MKTPLC*SRV", "amount": 156.80, "date": "2026-03-08"},
                        {"merchant": "DGTL MKTPLC*SRV", "amount": 156.80, "date": "2026-02-15"},
                    ]},
                    "get_transactions",
                    turn_number,
                )
            return (
                "I found the charge — there are two transactions from DGTL MKTPLC*SRV, "
                "both for $156.80. Do you recognize them?",
                messages + [{"role": "assistant", "content": "..."}],
                [{"tool": "get_card_details", "input": {}, "result": {}},
                 {"tool": "get_transactions", "input": {}, "result": {}}],
            )

        # Turn 2: user asks "what is my balance tho" — no new tools needed
        if turn_number == 2:
            return (
                "Your balance is $3,841.20.",
                messages + [{"role": "assistant", "content": "..."}],
                [],
            )

        # Turn 3: user says "maybe I am not sure" — no new tools
        if turn_number == 3:
            return (
                "No worries. Would you like me to dispute these charges?",
                messages + [{"role": "assistant", "content": "..."}],
                [],
            )

        return ("OK", messages, [])

    async def run():
        engine = ConversationEngine()

        # Auth flow
        await engine.process_turn("My credit card balance")  # greeting -> auth
        await engine.process_turn("646-555-0921")  # auth verify

        # Now patch ClaudeClient.run_tool_loop for the real turns
        engine.claude.run_tool_loop = mock_run_tool_loop
        # Disable hallucination blocker so it doesn't re-prompt
        from chatbot.guardrails.hallucination_blocker import ScanResult
        engine.hallucination_blocker.scan = lambda *a, **kw: ScanResult(safe=True, ungrounded_claims=[])

        with patch.object(engine.claude, "run_tool_loop", new=mock_run_tool_loop):
            # Turn 1: weird charge
            r1 = await engine.process_turn("There's a weird charge — $156.80 from DGTL something")
            assert "DGTL" in r1.response, f"Expected DGTL in response, got: {r1.response}"

            # Turn 2: asks about balance (should NOT repeat charges)
            r2 = await engine.process_turn("what is my current credit card balance tho")

            # Turn 3: "maybe I am not sure" (should NOT repeat anything)
            r3 = await engine.process_turn("maybe I am not sure")

        # --- ASSERTIONS ---

        def extract_facts_section(prompt: str) -> str:
            """Extract just the <verified_facts>...</verified_facts> block."""
            tag_open = "<verified_facts>\n"
            tag_close = "\n</verified_facts>"
            if tag_open not in prompt:
                return ""
            start = prompt.index(tag_open)
            end = prompt.index(tag_close, start) + len(tag_close)
            return prompt[start:end]

        # System prompt for turn 1: facts are NEW (first time presenting)
        facts_turn1 = extract_facts_section(captured_system_prompts[0])
        if facts_turn1:
            assert "ALREADY COMMUNICATED" not in facts_turn1, \
                f"Turn 1 facts should be NEW, got: {facts_turn1}"

        # System prompt for turn 2: facts from turn 1 should be ALREADY COMMUNICATED
        facts_turn2 = extract_facts_section(captured_system_prompts[1])
        assert "ALREADY COMMUNICATED" in facts_turn2, \
            f"Turn 2 should have ALREADY COMMUNICATED facts, got: {facts_turn2}"

        # System prompt for turn 3: everything still ALREADY COMMUNICATED
        facts_turn3 = extract_facts_section(captured_system_prompts[2])
        assert "ALREADY COMMUNICATED" in facts_turn3, \
            f"Turn 3 should have ALREADY COMMUNICATED facts, got: {facts_turn3}"
        # No NEW section in turn 3 (no new tools called)
        assert "[NEW" not in facts_turn3, \
            f"Turn 3 should have no NEW facts, got: {facts_turn3}"

        print("ALL ASSERTIONS PASSED")
        print()
        print("=== Turn 1 facts ===")
        print(facts_turn1 or "(no facts yet)")
        print()
        print("=== Turn 2 facts ===")
        print(facts_turn2)
        print()
        print("=== Turn 3 facts ===")
        print(facts_turn3)

    asyncio.run(run())


if __name__ == "__main__":
    test_fact_store_marks_presented()
    print("PASS: test_fact_store_marks_presented")

    test_new_facts_stay_new_old_stay_old()
    print("PASS: test_new_facts_stay_new_old_stay_old")

    test_system_prompt_contains_annotations()
    print("PASS: test_system_prompt_contains_annotations")

    test_conversation_marks_facts_after_response()
    print("PASS: test_conversation_marks_facts_after_response")
