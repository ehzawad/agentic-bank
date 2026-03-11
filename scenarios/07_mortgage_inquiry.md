# Scenario 07: Mortgage Pre-Approval & Rate Comparison

Customer exploring mortgage options for a home purchase. Complex multi-step inquiry with calculations, comparisons, and a workflow that gets deliberately paused.

## Systems Exercised
- Auth Gate
- FAQ Engine (all 3 tiers)
- Tool Executor (chained: credit_check → mortgage_estimate → rate_comparison)
- Workflow Engine (mortgage_preapproval — SUSPENDED by customer)
- Thread Tracker (complex slot filling)
- Hedge Enforcer G4 (rate estimates, approval likelihood)

---

## Conversation

### Turn 1
**Customer:** Good morning. My wife and I are looking to buy a house and we'd like to understand our mortgage options.
**Bot:** Good morning! Congratulations on the home search. I'd be happy to walk you through your options. Let me verify your identity first — could I have your phone number or account number?

> **State:** Greeting → Authenticating/CollectID

### Turn 2
**Customer:** Phone is 718-555-0412.
**Bot:** Thank you, one moment.

> **Tool Call:** `verify(phone="7185550412")`
> **API Response:** `{verified: true, name: "Robert & Lisa Chen", accounts: ["joint_checking_4402", "joint_savings_9918"], segment: "premier", tenure: "7yr", existing_mortgage: false}`
> **Session Store:** Robert & Lisa Chen, premier, joint accounts, 7yr, no existing mortgage

**Bot:** Welcome, Mr. Chen. I can see your joint accounts with us. Have you and your wife identified a price range for the home, or are you still exploring?

### Turn 3
**Customer:** We're looking at homes in the $550,000 to $650,000 range. We've saved about $130,000 for the down payment.
**Bot:** That's a solid down payment. Let me check your pre-approval options.

> **State:** ToolAction/Chaining
> **LLM Pass 1:**
> ```json
> {
>   "resolved_query": "mortgage pre-approval for $550K-$650K home, $130K down payment",
>   "action_type": "tool_call",
>   "tool_call": [
>     {"function": "check_mortgage_eligibility", "params": {"customer_id": "robert_chen_4402", "home_price_range": [550000, 650000], "down_payment": 130000}}
>   ],
>   "filler": "That's a solid down payment. Let me check your pre-approval options.",
>   "emotion_read": "positive"
> }
> ```
> **Tool Result:**
> ```json
> {
>   "eligible": true,
>   "max_approved": 620000,
>   "down_payment_pct_at_max": 20.97,
>   "rates": {
>     "30yr_fixed": 6.375,
>     "15yr_fixed": 5.750,
>     "7_1_arm": 5.500
>   },
>   "estimated_monthly": {
>     "30yr_at_550k": {"principal_interest": 2621, "tax_insurance": 650, "total": 3271},
>     "30yr_at_620k": {"principal_interest": 3057, "tax_insurance": 730, "total": 3787},
>     "15yr_at_550k": {"principal_interest": 3495, "tax_insurance": 650, "total": 4145}
>   }
> }
> ```
> **Fact Store Written:** mortgage eligible, max=620K, rates, monthly estimates @ turn3

**Bot:** Great news. Based on your profile, you're pre-approved for up to $620,000. With your $130,000 down payment, that's about 21% down — which means no private mortgage insurance required. Here are your rate options:

| Loan Type | Rate | Monthly Payment ($550K home) | Monthly Payment ($620K home) |
|-----------|------|------------------------------|------------------------------|
| 30-year fixed | 6.375% | ~$3,271 | ~$3,787 |
| 15-year fixed | 5.750% | ~$4,145 | — |
| 7/1 ARM | 5.500% | lower initially | — |

These include estimated property tax and insurance. Would you like me to break any of these down further?

### Turn 4
**Customer:** What's the difference between the 30-year fixed and the ARM? I've heard mixed things about adjustable rates.
**Bot:** Good question — let me explain.

> **FAQ Search:** "30 year fixed vs adjustable rate mortgage ARM comparison" → confidence = 0.83 → **BLENDED**
> **FAQ Base:** "30yr fixed: rate locked for full term, predictable payments. 7/1 ARM: fixed for first 7 years, then adjusts annually based on market index + margin. Caps typically 2% per adjustment, 5% lifetime."
> **G4 Hedge Enforcer:** HEDGED flag (0.83 confidence)

**Bot:** The 30-year fixed locks your rate at 6.375% for the entire loan — your payment never changes, which makes budgeting straightforward. The 7/1 ARM starts lower at 5.500% for the first 7 years, then adjusts annually based on market rates. Adjustments are typically capped at 2% per year with a 5% lifetime cap.

The ARM generally makes more sense if you plan to sell or refinance within 7 years. If you're planning to stay long-term, the 30-year fixed is usually the safer choice. That said, it depends on your specific situation and risk tolerance — I'd recommend discussing the ARM option with a mortgage advisor if you're seriously considering it.

### Turn 5
**Customer:** We plan to stay at least 15-20 years, so the 30-year fixed sounds right. Can we start the pre-approval process?
**Bot:** Absolutely. I'll start the formal pre-approval. I'll need a few details.

> **State:** Listening → WorkflowActive/WaitUser
> **Workflow:** mortgage_preapproval Step 1: Collect employment & income details
> **Thread Tracker:** mortgage_preapproval ACTIVE, slots needed: [employment, combined_income, other_debts]

**Bot:** First, could you tell me about your employment? Are you both employed, and roughly what's your combined annual household income?

### Turn 6
**Customer:** I'm a software engineer at a bank, $145,000 a year. Lisa is a pediatrician, she makes about $195,000.
**Bot:** Combined $340,000 — that's very strong. Do you have any existing debts? Car loans, student loans, other obligations?

> **Slots filled:** [robert_employment=software_engineer, robert_income=145000, lisa_employment=pediatrician, lisa_income=195000, combined=340000]

### Turn 7
**Customer:** We have one car payment, about $450 a month. That's it. Oh — I just realized, I have to pick my wife up in 10 minutes. Can we finish this later?
**Bot:** Of course, Mr. Chen. I've saved everything so far — your pre-approval status, the rates we discussed, and the details you've provided. When you call back, just verify your identity and we'll pick up right where we left off. No need to repeat anything. The pre-approved rates are held for 60 days.

> **State:** WorkflowActive → Suspended
> **Workflow:** mortgage_preapproval SUSPENDED at Step 1 (partially filled)
> **Thread Tracker:** mortgage_preapproval SUSPENDED, slots filled: [employment, income, car_payment=450/mo], slots needed: [other_debts_confirmed, property_address_if_known, consent_to_hard_pull]
> **All memory stores updated — full state preserved for resume**

### Turn 8
**Customer:** Perfect, thank you! We'll call back tonight or tomorrow.
**Bot:** Take your time. Everything is saved. Have a good afternoon, Mr. Chen!

> **State:** Farewell
