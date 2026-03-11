# Scenario 03: Unauthorized Transaction & Emergency Card Block

Customer reports suspicious transactions and triggers an emergency card blocking workflow. High urgency conversation with emotion tracking.

## Systems Exercised
- Auth Gate (expedited for fraud)
- Tool Executor (get_transactions, block_card)
- Workflow Engine (fraud_report flow)
- Emotion Tracker (anxious → stressed)
- Emotion Escalation G5
- Fact Store (transaction data, block confirmation)
- Proactive recommendation pattern

---

## Conversation

### Turn 1
**Customer:** I think someone's been using my card! I see charges I didn't make!
**Bot:** I understand your concern, and I'll help you right away. Let me verify your identity first so I can secure your account. Could you provide your phone number or card number?

> **State:** Greeting → Authenticating/CollectID
> **Emotion Tracker:** anxious (first read — urgency detected in input)
> **LLM Pass 1:** emotion_read: anxious, tone adjustment: empathetic + urgent

### Turn 2
**Customer:** 646-555-0317. Please hurry!
**Bot:** Verifying now — this will just take a moment.

> **Tool Call:** `verify(phone="6465550317")`
> **API Response:** `{verified: true, name: "David Okonkwo", accounts: ["checking_8912"], cards: ["visa_ending_4455", "debit_ending_7821"], segment: "citigold", tenure: "8yr"}`
> **Session Store:** David Okonkwo, Citigold, checking, visa_4455 + debit_7821, verified

**Bot:** Mr. Okonkwo, I've verified your identity. Which card are you seeing the suspicious charges on — your Visa ending in 4455 or your debit card ending in 7821?

### Turn 3
**Customer:** The Visa, 4455. There are three charges from today that aren't mine!
**Bot:** Let me pull up today's transactions on that card immediately.

> **State:** ToolAction/Executing
> **LLM Pass 1:**
> ```json
> {
>   "resolved_query": "get today's transactions on Visa ending 4455 to identify unauthorized charges",
>   "action_type": "tool_call",
>   "tool_call": {"function": "get_transactions", "params": {"card": "visa_4455", "date": "2026-03-11"}},
>   "filler": "Let me pull up today's transactions on that card immediately.",
>   "emotion_read": "stressed"
> }
> ```
> **Tool Result:**
> ```json
> {
>   "transactions": [
>     {"id": "TXN-71001", "time": "06:12", "amount": -249.99, "merchant": "BESTBUY.COM", "location": "online"},
>     {"id": "TXN-71002", "time": "06:45", "amount": -189.50, "merchant": "NIKE STORE #892", "location": "Chicago, IL"},
>     {"id": "TXN-71003", "time": "07:30", "amount": -420.00, "merchant": "ELECTRONICS HUB", "location": "Chicago, IL"},
>     {"id": "TXN-71004", "time": "08:15", "amount": -34.50, "merchant": "STARBUCKS #1204", "location": "New York, NY"}
>   ]
> }
> ```
> **Fact Store Written:** 4 transactions on visa_4455 today @ turn3

**Bot:** I can see four transactions on your Visa today:
1. $249.99 at BestBuy.com (online) at 6:12 AM
2. $189.50 at Nike Store in Chicago at 6:45 AM
3. $420.00 at Electronics Hub in Chicago at 7:30 AM
4. $34.50 at Starbucks in New York at 8:15 AM

Which of these are not yours?

### Turn 4
**Customer:** The first three! I'm in New York, I wasn't in Chicago! Only the Starbucks one is mine!
**Bot:** I see that clearly — three charges totaling $859.49 in a different city. I'd strongly recommend we block this card immediately to prevent any further unauthorized use. Shall I block it right now?

> **State:** ToolAction → proactive recommendation
> **Emotion Tracker:** stressed (trajectory: anxious → stressed over 2 turns)
> **LLM Pass 1:**
> ```json
> {
>   "resolved_query": "3 unauthorized transactions totaling $859.49 on visa_4455, customer in NYC but charges in Chicago",
>   "action_type": "talk",
>   "talk_type": "proactive_recommendation",
>   "recommendation": "block card immediately",
>   "emotion_read": "stressed"
> }
> ```
> **Note:** Bot proactively suggests blocking rather than waiting for customer to ask

### Turn 5
**Customer:** Yes, block it now!
**Bot:** Blocking your card right now.

> **State:** WorkflowActive/StepExec
> **Workflow:** fraud_report flow triggered
> **Step 1:** Block card (auto — user confirmed)
> **Tool Call:** `block_card(card="visa_4455", reason="suspected_fraud", reported_txns=["TXN-71001","TXN-71002","TXN-71003"])`
> **API Response:** `{status: "blocked", block_id: "BLK-20260311-4455", blocked_at: "2026-03-11T10:32:00Z", replacement_eligible: true}`
> **Fact Store Written:** visa_4455 BLOCKED, block_id=BLK-20260311-4455 @ turn5

**Bot:** Done. Your Visa ending in 4455 has been blocked effective immediately. No further charges can go through. Your block reference is BLK-20260311-4455. Now let me file the dispute for those three unauthorized charges. I'll need to confirm a couple of things.

> **Workflow Step 2:** File dispute (needs_input)

### Turn 6
**Customer:** Okay, what do you need?
**Bot:** When was the last time you had physical possession of your card — is it still with you, or could it have been lost or stolen?

> **Thread Tracker:** fraud_report ACTIVE, slots filled: [card, unauthorized_txns, block_confirmed], slots needed: [card_possession, last_authorized_use]

### Turn 7
**Customer:** I have the card right here in my wallet. I never lost it. These must be from my card number being stolen online or something.
**Bot:** Understood — card present, suspected number compromise. And the Starbucks charge at 8:15 AM this morning was the last one you actually made?

> **Slots filled:** [card_possession=in_hand, fraud_type=card_not_present]
> **Slots needed:** [last_authorized_use_confirmed]

### Turn 8
**Customer:** Yes, that's correct.
**Bot:** Filing your dispute now.

> **Workflow Step 3:** Submit dispute (auto)
> **Tool Call:** `file_dispute({card: "visa_4455", disputed_txns: ["TXN-71001","TXN-71002","TXN-71003"], total: 859.49, fraud_type: "card_not_present", card_possession: "in_hand", last_auth_txn: "TXN-71004"})`
> **API Response:** `{dispute_id: "DSP-2026-08847", status: "under_investigation", provisional_credit: true, credit_amount: 859.49, estimated_resolution: "10 business days"}`
> **Fact Store Written:** dispute_id=DSP-2026-08847, provisional_credit=859.49 @ turn8

**Bot:** Your dispute has been filed. Here's a summary:
- **Dispute ID:** DSP-2026-08847
- **Amount disputed:** $859.49 across 3 transactions
- **Provisional credit:** $859.49 will be applied to your account within 1-2 business days while we investigate
- **Estimated resolution:** 10 business days

Would you like us to send a replacement card?

### Turn 9
**Customer:** Yes please. How long will that take?
**Bot:** Let me order that for you.

> **Workflow Step 4:** Order replacement (auto + faq)
> **Tool Call:** `order_replacement_card(card="visa_4455", shipping="expedited")`
> **API Response:** `{replacement_card: "visa_ending_6692", shipping: "expedited", eta: "2-3 business days", temp_virtual_card: true}`
> **FAQ Search:** "replacement card delivery time expedited" → confidence = 0.89 → **PURE FAQ**

**Bot:** Your replacement card ending in 6692 is on the way with expedited shipping — you should have it within 2 to 3 business days. In the meantime, I've also activated a temporary virtual card number that you can use immediately for online purchases. You'll find it in your Citi mobile app under "Virtual Card." Is there anything else I can help you with?

### Turn 10
**Customer:** No, I think that covers it. Thank you for handling this so quickly.
**Bot:** Of course, Mr. Okonkwo. I'm sorry this happened, but everything is secured now. If you notice any other suspicious activity, don't hesitate to call us immediately. Have a safe day.

> **State:** Farewell
> **Workflow:** fraud_report COMPLETE
> **Emotion Tracker:** stressed → relieved (trajectory improving)
> **Final memory update across all 5 stores**
