"""Live conversation test — runs against real Claude API.

Replays the exact scenario from the user's demo and prints responses
to check for unnatural repetition.
"""

import asyncio
from chatbot.engine.conversation import ConversationEngine


CONVERSATION = [
    ("My credit card balance", "AUTH GREETING"),
    ("646-555-0921", "AUTH VERIFY"),
    ("There's a weird charge on my credit card — $156.80 from DGTL something", "CHARGE INQUIRY"),
    ("what is my current credit card balance tho", "BALANCE QUESTION (should NOT repeat charge info)"),
    ("maybe I am not sure", "UNCERTAIN RESPONSE (should NOT repeat balance or charges)"),
]


async def main():
    engine = ConversationEngine()
    any_issues = 0

    for i, (user_msg, label) in enumerate(CONVERSATION, 1):
        print(f"\n{'='*70}")
        print(f"TURN {i}: {label}")
        print(f"{'='*70}")
        print(f"USER: {user_msg}")
        print()

        # Show what facts Claude will see BEFORE this turn
        facts_ctx = engine.fact_store.to_context()
        if facts_ctx and i >= 3:
            print(f"  [FACTS IN SYSTEM PROMPT]:")
            for line in facts_ctx.split("\n"):
                print(f"    {line}")
            print()

        result = await engine.process_turn(user_msg)

        print(f"BOT:  {result.response}")
        print(f"  [state={result.state}, emotion={result.emotion}, "
              f"tools={[tc['tool'] for tc in result.tool_calls]}]")

        # Flag repetition issues (strict: re-stating specifics, not brief topic refs)
        if i >= 4:
            resp_lower = result.response.lower()
            issues = []
            if i == 4:  # "what is my balance" turn
                # Re-stating charge AMOUNTS or DATES is bad; mentioning "the charge" is fine
                if "156.80" in resp_lower or "156" in resp_lower:
                    issues.append("REPEATED charge amount from earlier turn")
                if "march 8" in resp_lower or "february 15" in resp_lower:
                    issues.append("REPEATED charge dates from earlier turn")
                if "txn-" in resp_lower:
                    issues.append("REPEATED transaction IDs from earlier turn")
            if i == 5:  # "maybe I am not sure" turn
                if "$3,841" in result.response or "3841" in resp_lower or "3,841" in resp_lower:
                    issues.append("REPEATED balance amount from earlier turn")
                if "156.80" in resp_lower or "156" in resp_lower:
                    issues.append("REPEATED charge amount from earlier turn")
                if "march" in resp_lower or "february" in resp_lower:
                    issues.append("REPEATED dates from earlier turn")

            if issues:
                any_issues += 1
                print(f"\n  *** REPETITION DETECTED ***")
                for issue in issues:
                    print(f"  !!! {issue}")
            else:
                print(f"\n  OK — no unwanted repetition")

    # Tally
    print(f"\n{'='*70}")
    if any_issues:
        print(f"RESULT: {any_issues} turn(s) with repetition issues")
    else:
        print("RESULT: CLEAN — no unwanted repetition detected")
    print(f"{'='*70}")


if __name__ == "__main__":
    asyncio.run(main())
