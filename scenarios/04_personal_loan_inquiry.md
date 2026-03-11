# Scenario 04: Personal Loan Inquiry & EMI Calculation

Customer asks about personal loan options, eligibility, and wants an EMI estimate. Demonstrates tool chaining and blended FAQ.

## Systems Exercised
- Auth Gate
- FAQ Engine (Pure FAQ + Blended)
- Tool Executor (chained: check_loan_eligibility → calculate_emi)
- Fact Store (eligibility data, EMI calculations)
- Thread Tracker (single topic with deepening detail)
- Hedge Enforcer G4

---

## Conversation

### Turn 1
**Customer:** Hi, I'd like to know about personal loans.
**Bot:** Hello! Welcome to HSBC. I'd be happy to walk you through our personal loan options. Let me verify your identity first — could I have your phone number or account number?

> **State:** Greeting → Authenticating/CollectID

### Turn 2
**Customer:** My account number is 8834-2210.
**Bot:** Thank you, one moment.

> **Tool Call:** `verify(account="88342210")`
> **API Response:** `{verified: true, name: "Maria Santos", accounts: ["checking_8834", "savings_2210"], segment: "advance", tenure: "3yr", credit_score_band: "excellent"}`
> **Session Store:** Maria Santos, Advance segment, checking+savings, 3yr, excellent credit

**Bot:** Thank you, Ms. Santos. What are you looking to use the personal loan for? That can help me point you toward the best option.

### Turn 3
**Customer:** I'm renovating my kitchen. Probably need around $25,000.
**Bot:** Got it. Let me pull up our personal loan rates for home improvement.

> **State:** FAQLookup/Searching
> **FAQ Search:** "personal loan home improvement rates" → confidence = 0.88 → **PURE FAQ**
> **FAQ Result:** "HSBC Personal Loan for home improvement: $5,000-$50,000, terms 12-60 months, APR from 6.99%-12.99% based on creditworthiness, no collateral required, no prepayment penalty."

**Bot:** For home improvement, our personal loans range from $5,000 to $50,000 with terms of 12 to 60 months. The APR starts at 6.99% and goes up to 12.99% depending on your credit profile. There's no collateral required and no prepayment penalty. Would you like me to check what rate you'd qualify for?

### Turn 4
**Customer:** Yes, please! And what would my monthly payment be for $25,000?
**Bot:** Let me check your eligibility and run those numbers.

> **State:** ToolAction/Chaining
> **LLM Pass 1:**
> ```json
> {
>   "resolved_query": "check loan eligibility and calculate monthly payment for $25,000 personal loan",
>   "action_type": "tool_call",
>   "tool_call": [
>     {"function": "check_loan_eligibility", "params": {"customer_id": "maria_santos_8834", "amount": 25000, "purpose": "home_improvement"}},
>     {"function": "calculate_emi", "params": {"amount": 25000, "depends_on": "check_loan_eligibility.approved_rate"}}
>   ],
>   "filler": "Let me check your eligibility and run those numbers.",
>   "emotion_read": "positive"
> }
> ```
> **Tool Chain:**
> **Step 1:** `check_loan_eligibility` → `{eligible: true, approved_amount: 30000, offered_rate: 7.49, term_options: [24, 36, 48, 60]}`
> **Step 2 (triggered by step 1):** `calculate_emi({amount: 25000, rate: 7.49, terms: [36, 48, 60]})` → `{emi_36mo: 776.33, emi_48mo: 604.29, emi_60mo: 501.18}`
> **Fact Store Written:** eligible, approved_up_to=30000, rate=7.49%, EMIs calculated @ turn4

**Bot:** Great news, Ms. Santos. You're pre-approved for up to $30,000 at 7.49% APR. For your $25,000 request, here are your monthly payment options:

| Term | Monthly Payment | Total Interest |
|------|----------------|----------------|
| 36 months | $776.33 | $2,947.88 |
| 48 months | $604.29 | $4,005.92 |
| 60 months | $501.18 | $5,070.80 |

Which term works best for your budget?

### Turn 5
**Customer:** The 48-month option looks good. What documents would I need?
**Bot:** Good choice. Let me get the document requirements.

> **FAQ Search:** "personal loan required documents" → confidence = 0.92 → **PURE FAQ**

**Bot:** For the 48-month option at $604.29 per month, you'd need:
1. Government-issued photo ID
2. Proof of income — last two pay stubs or recent tax return
3. Proof of address — utility bill or bank statement within 90 days
4. Home improvement contractor estimate or quote (since it's for renovation)

Since you already bank with us, we have most of your information on file. Would you like to start the application?

### Turn 6
**Customer:** I'm self-employed actually. Is that going to be a problem?
**Bot:** Not at all.

> **FAQ Search:** "personal loan self-employed income verification" → confidence = 0.68 → **BLENDED**
> **FAQ Base:** "Self-employed applicants: 2 years of tax returns, profit & loss statement, or business bank statements showing 12 months of deposits."
> **G4 Hedge Enforcer:** HEDGED flag injected

**Bot:** Self-employment isn't typically an issue. In most cases, we'd ask for your last two years of tax returns or a profit and loss statement, along with 12 months of business bank statements showing regular income. Your pre-approval rate may be subject to final verification of these documents, but based on your account history with us, things generally look positive. Would you like to proceed?

> **Note:** "typically", "in most cases", "generally" — hedge language enforced

### Turn 7
**Customer:** Let me think about it and gather the documents first. Can I come back and pick up where I left off?
**Bot:** Absolutely, Ms. Santos. Your pre-approval is valid for 30 days, and I've noted everything from our conversation. When you're ready, just call back and reference your checking account — we'll have all the details on file. The pre-approved rate of 7.49% will be held for you during that period. Take your time!

> **State:** Farewell
> **Thread Tracker:** personal_loan_inquiry SUSPENDED (customer choice, not topic switch)
> **All memory stores updated — pre-approval details preserved for return visit**

### Turn 8
**Customer:** Perfect, thank you!
**Bot:** You're welcome! Good luck with the kitchen renovation. We're here whenever you're ready.

> **State:** Farewell → session end
