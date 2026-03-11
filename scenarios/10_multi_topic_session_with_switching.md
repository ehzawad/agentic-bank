# Scenario 10: Multi-Topic Session with Topic Switching

Customer starts with one question, switches topics mid-conversation, starts a workflow, interrupts it with a side question, and resumes. Stress-tests the thread tracker and suspend/resume logic.

## Systems Exercised
- Auth Gate
- Thread Tracker (multiple concurrent threads, suspend/resume)
- FAQ Engine (side questions during workflow)
- Tool Executor (balance check mid-workflow)
- Workflow Engine (dispute_flow — suspended and resumed)
- Dialogue State Machine (full state transitions including Suspended → Listening → WorkflowActive)
- All 5 memory stores under concurrent thread pressure
- Clarifying state (ambiguous input)

---

## Conversation

### Turn 1
**Customer:** Hey, couple of things I need help with today.
**Bot:** Hello! Happy to help. Let me verify your identity first, and then we can work through everything. Could I have your phone number?

> **State:** Greeting → Authenticating/CollectID

### Turn 2
**Customer:** 646-555-0921
**Bot:** Thank you, one moment.

> **Tool Call:** `verify(phone="6465550921")`
> **API Response:** `{verified: true, name: "Jennifer Park", accounts: ["checking_3301", "savings_8850", "credit_card_ending_2277"], segment: "preferred", tenure: "5yr"}`
> **Session Store:** Jennifer Park, preferred, checking+savings+credit, 5yr

**Bot:** Thank you, Ms. Park. What's the first thing you'd like to help with?

### Turn 3
**Customer:** First, there's a charge on my credit card I want to dispute. $156.80 from some company I've never heard of.
**Bot:** Let me find that transaction.

> **State:** Listening/Ready → ToolAction/Executing
> **Thread Tracker:** Thread 1: dispute_inquiry ACTIVE, slots needed: [transaction_id, merchant, reason]
> **LLM Pass 1:**
> ```json
> {
>   "resolved_query": "find $156.80 charge on credit card ending 2277 from unknown merchant",
>   "action_type": "tool_call",
>   "tool_call": {"function": "get_transactions", "params": {"card": "credit_2277", "amount_filter": 156.80}},
>   "filler": "Let me find that transaction.",
>   "emotion_read": "neutral"
> }
> ```
> **Tool Result:**
> ```json
> {
>   "transactions": [
>     {"id": "TXN-55091", "date": "2026-03-08", "amount": -156.80, "merchant": "DGTL MKTPLC*SRV", "category": "digital_services"},
>     {"id": "TXN-54220", "date": "2026-02-15", "amount": -156.80, "merchant": "DGTL MKTPLC*SRV", "category": "digital_services"}
>   ]
> }
> ```
> **Fact Store Written:** 2 charges from DGTL MKTPLC*SRV, $156.80 each @ turn3

**Bot:** I found two charges of $156.80 from "DGTL MKTPLC*SRV" — one from March 8 and an earlier one from February 15. This looks like it could be a recurring subscription from a digital marketplace. Do you want to dispute both, or just the most recent one?

### Turn 4
**Customer:** Both! I never signed up for whatever that is. Actually wait — what's my checking account balance? I need to make sure I have enough for rent tomorrow.

> **State:** ToolAction → topic switch detected!
> **Thread Tracker:**
>   - Thread 1: dispute_inquiry SUSPENDED (need: [dispute_both_confirmed, reason_detail])
>   - Thread 2: balance_check ACTIVE
> **LLM Pass 1:** Detects topic switch, suspends dispute, handles balance check

**Bot:** Let me check your balance — and we'll come right back to the dispute.

> **Tool Call:** `get_balance(account="checking_3301")`
> **API Response:** `{account: "checking_3301", balance: 4215.60, currency: "USD", as_of: "2026-03-11T11:00:00Z"}`
> **Fact Store Written:** checking balance=4215.60 @ turn4

**Bot:** Your checking account balance is $4,215.60 as of this morning. Now, back to the dispute — you'd like to dispute both $156.80 charges from DGTL MKTPLC. Can you confirm you've never authorized this company to charge your card?

> **Thread Tracker:** Thread 2: balance_check RESOLVED → Thread 1: dispute_inquiry RESUMED
> **Note:** Bot smoothly handles the interruption and naturally returns to the suspended thread

### Turn 5
**Customer:** Correct, never heard of them. Never authorized anything.
**Bot:** Understood. I'll start the dispute process for both charges.

> **State:** Listening → WorkflowActive/StepExec
> **Workflow:** dispute_flow triggered
> **Step 1:** File dispute (auto — all slots now filled)
> **Tool Call:** `file_dispute({card: "credit_2277", disputed_txns: ["TXN-55091", "TXN-54220"], total: 313.60, reason: "unauthorized_recurring_charge", merchant: "DGTL MKTPLC*SRV"})`
> **API Response:** `{dispute_id: "DSP-2026-11042", status: "under_investigation", provisional_credit: true, credit_amount: 313.60, estimated_resolution: "10 business days"}`
> **Fact Store Written:** dispute DSP-2026-11042, provisional credit $313.60 @ turn5

**Bot:** Both charges are now disputed. Here's your summary:
- **Dispute ID:** DSP-2026-11042
- **Total disputed:** $313.60 (two charges of $156.80)
- **Provisional credit:** $313.60 will appear on your next statement
- **Estimated resolution:** 10 business days

I'd also recommend we block that merchant from charging your card again. Shall I do that?

> **Proactive recommendation — prevent recurring unauthorized charges**

### Turn 6
**Customer:** Yes, block them. Oh, and one more thing — what's the interest rate on my credit card? I've been carrying a balance and it seems really high.

> **Thread Tracker:**
>   - Thread 1: dispute_inquiry → merchant block substep ACTIVE
>   - Thread 3: credit_card_rate_inquiry QUEUED (side question is FAQ)

> **Tool Call:** `block_merchant(card="credit_2277", merchant_id="DGTL_MKTPLC_SRV")`
> **API Response:** `{blocked: true, merchant: "DGTL MKTPLC*SRV"}`

> **FAQ Search:** "credit card interest rate APR" → confidence = 0.70 → **BLENDED**
> **G4 Hedge Enforcer:** HEDGED flag
> **Note:** Bot handles both the merchant block and the FAQ question in one turn

**Bot:** Done — DGTL MKTPLC is permanently blocked from your card.

As for your interest rate, your current APR is typically determined by your card agreement and credit profile. For most preferred-tier customers, it generally falls in the 18-22% range. Let me pull your exact rate.

> **Tool Call:** `get_card_details(card="credit_2277")`
> **API Response:** `{card: "credit_2277", apr_purchase: 19.99, apr_cash_advance: 24.99, credit_limit: 15000, current_balance: 3841.20}`
> **Fact Store Written:** APR=19.99%, balance=3841.20 @ turn6

**Bot:** Your purchase APR is 19.99% and cash advance APR is 24.99%. Your current balance is $3,841.20. If the rate feels high, you may be eligible for a balance transfer to a lower-rate card. Would you like me to check your options?

> **Thread Tracker:**
>   - Thread 1: dispute COMPLETE (filed + merchant blocked)
>   - Thread 3: credit_card_rate_inquiry ACTIVE → potential balance_transfer_inquiry

### Turn 7
**Customer:** Hmm, maybe. What would a balance transfer look like?
**Bot:** Let me check what's available for you.

> **FAQ Search:** "balance transfer options lower interest rate" → confidence = 0.55 → **PURE LLM**

**Bot:** Balance transfers let you move your existing $3,841.20 to a card with a promotional low or 0% APR for an introductory period, usually 12 to 18 months. There's typically a transfer fee of 3-5% of the amount. Whether it makes sense depends on how quickly you plan to pay it down. I'd recommend speaking with our credit card team who can pull up specific offers available to you right now — they'd have access to any promotional rates we're currently running. Would you like me to connect you, or is that something you'd like to explore on your own?

> **Note:** Pure LLM fallback — specific promotional offers are not in the FAQ. Appropriate disclaimer and suggestion to connect with specialist.

### Turn 8
**Customer:** I'll look into it myself online. Let me ask you one last thing — you said my savings has an account too, right? What's the balance there?
**Bot:** Let me check.

> **Thread Tracker:** Thread 3: rate_inquiry RESOLVED (customer deferred). Thread 4: savings_balance ACTIVE
> **Tool Call:** `get_balance(account="savings_8850")`
> **API Response:** `{account: "savings_8850", balance: 22140.00, currency: "USD", as_of: "2026-03-11T11:00:00Z"}`
> **Fact Store Written:** savings balance=22140.00 @ turn8

**Bot:** Your savings account balance is $22,140.00. Is there anything else you need?

### Turn 9
**Customer:** Nope, I think that's everything. We covered a lot! Thanks!
**Bot:** We sure did! Just to recap what we handled today:
1. Disputed two unauthorized charges totaling $313.60 — provisional credit coming
2. Blocked the merchant from future charges
3. Checked your checking balance ($4,215.60) and savings ($22,140.00)
4. Reviewed your credit card APR (19.99%)

Your dispute reference is DSP-2026-11042 if you need it. Have a great day, Ms. Park!

> **State:** Farewell
> **Thread Tracker final state:**
>   - Thread 1: dispute_inquiry COMPLETE
>   - Thread 2: balance_check COMPLETE
>   - Thread 3: credit_card_rate_inquiry RESOLVED (deferred by customer)
>   - Thread 4: savings_balance COMPLETE
> **All 5 memory stores updated with full multi-topic session**
