# Scenario 01: Balance Inquiry & Recent Transactions

Customer calls to check their account balance, then drills into a specific transaction they don't recognize.

## Systems Exercised
- Auth Gate (phone verification)
- Tool Executor (get_balance, get_transactions)
- Fact Store (balance, transaction data written by tool results)
- Two-pass LLM (resolve + naturalize)
- Hallucination Blocker G1 (financial data must come from tools)
- Thread Tracker (topic: balance_inquiry → transaction_lookup)

---

## Conversation

### Turn 1
**Customer:** Hi, I need to check my account balance.
**Bot:** Welcome to HSBC. I'd be happy to help you with that. Could I have your phone number or account number to verify your identity?

> **State:** Greeting → Authenticating/CollectID
> **Action:** talk (greeting + ask for verification)

### Turn 2
**Customer:** Sure, it's 917-555-0142.
**Bot:** Thank you. Let me verify that for you.

> **State:** Authenticating/Verify
> **Tool Call:** `verify(phone="9175550142")`
> **API Response:** `{verified: true, name: "James Chen", accounts: ["checking_4821", "savings_7903"], segment: "premier", tenure: "5yr"}`
> **Session Store Written:** James Chen, premier, checking+savings, verified, 5yr customer
> **Bot (after verify):** Thank you, Mr. Chen. I can see your accounts. Would you like the balance for your checking account, savings account, or both?

### Turn 3
**Customer:** Just checking, please.
**Bot:** Let me pull that up for you.

> **State:** Listening/Ready → ToolAction/Executing
> **LLM Pass 1 Output:**
> ```json
> {
>   "resolved_query": "get checking account balance",
>   "action_type": "tool_call",
>   "tool_call": {"function": "get_balance", "params": {"account": "checking_4821"}},
>   "filler": "Let me pull that up for you.",
>   "emotion_read": "neutral"
> }
> ```
> **Filler streamed immediately**
> **Tool Result:** `{account: "checking_4821", balance: 12450.75, currency: "USD", as_of: "2026-03-11T10:00:00Z"}`
> **Fact Store Written:** balance=12450.75 USD @ turn3
> **LLM Pass 2:** Naturalizes ground truth
> **G1 Check:** Financial data came from tool ✓

**Bot:** Your checking account balance is $12,450.75 as of this morning. Is there anything else you'd like to know?

### Turn 4
**Customer:** Actually yeah, I see a charge for $89.99 from yesterday that I don't recognize. Can you tell me what that is?
**Bot:** Let me look into yesterday's transactions for you.

> **State:** Listening/Ready → ToolAction/Executing
> **Thread Tracker:** balance_inquiry RESOLVED, transaction_lookup ACTIVE (slots needed: date, amount)
> **LLM Pass 1 Output:**
> ```json
> {
>   "resolved_query": "identify unrecognized charge $89.99 from yesterday",
>   "action_type": "tool_call",
>   "tool_call": {"function": "get_transactions", "params": {"account": "checking_4821", "date": "2026-03-10", "amount_filter": 89.99}},
>   "filler": "Let me look into yesterday's transactions for you.",
>   "emotion_read": "concerned"
> }
> ```
> **Tool Result:** `{transactions: [{id: "TXN-90812", date: "2026-03-10", amount: -89.99, merchant: "AMZN Digital*RT4K92", category: "digital_services", description: "Amazon Prime + Add-on subscription renewal"}]}`
> **Fact Store Written:** TXN-90812, AMZN Digital, -89.99, Amazon Prime renewal @ turn4

**Bot:** I found that charge. It's a $89.99 transaction from Amazon Digital Services, posted yesterday. It appears to be an Amazon Prime subscription renewal with an add-on. Does that ring a bell?

### Turn 5
**Customer:** Oh right, my wife must have signed up for something. That's fine then. Thanks!
**Bot:** No problem at all, Mr. Chen. Glad we could clear that up. Is there anything else I can help you with today?

> **State:** Listening/Ready
> **Thread Tracker:** transaction_lookup RESOLVED
> **Emotion Tracker:** concerned → neutral (resolved)

### Turn 6
**Customer:** No, that's everything. Thanks!
**Bot:** You're welcome, Mr. Chen. Have a great day!

> **State:** Farewell
> **All memory stores updated with session summary**
