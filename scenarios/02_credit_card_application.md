# Scenario 02: Credit Card Application Journey

Customer inquires about credit card eligibility, required documents, and starts the application workflow.

## Systems Exercised
- Auth Gate
- FAQ Engine (all 3 tiers: Pure FAQ, Blended, Pure LLM)
- Workflow Engine (credit_card_application flow)
- Hedge Enforcer G4 (medium-confidence answers)
- Dialogue State Machine (FAQLookup → WorkflowActive)
- Slot filling in Thread Tracker

---

## Conversation

### Turn 1
**Customer:** Hello, I'm interested in applying for a credit card.
**Bot:** Welcome to Citibank! I'd love to help you explore your credit card options. First, let me verify your identity. Could I have your phone number or account number?

> **State:** Greeting → Authenticating/CollectID

### Turn 2
**Customer:** 212-555-0198
**Bot:** Thank you. One moment please.

> **Tool Call:** `verify(phone="2125550198")`
> **API Response:** `{verified: true, name: "Priya Sharma", accounts: ["savings_3301"], segment: "standard", tenure: "2yr", credit_score_band: "good"}`
> **Session Store:** Priya Sharma, standard, savings, verified, 2yr, credit_score: good

**Bot:** Thank you, Ms. Sharma. I can see you've been with us for two years. What kind of credit card are you looking for — cashback, travel rewards, or something else?

### Turn 3
**Customer:** I travel a lot for work. What do you have for that?
**Bot:** Let me look up our travel card options for you.

> **State:** Listening → FAQLookup/Searching
> **LLM Pass 1:**
> ```json
> {
>   "resolved_query": "travel rewards credit card options",
>   "action_type": "faq",
>   "filler": "Let me look up our travel card options for you.",
>   "emotion_read": "neutral"
> }
> ```
> **FAQ Search:** confidence = 0.91 → **PURE FAQ**
> **FAQ Result:** "Citi PremierMiles: 2 miles/dollar, no foreign transaction fee, airport lounge access, $95 annual fee. Citi Prestige: 3 miles/dollar on travel, Priority Pass, 4th night free hotel, $495 annual fee."
> **LLM Pass 2:** Wraps naturally

**Bot:** We have two main travel cards. The Citi PremierMiles gives you 2 miles per dollar with no foreign transaction fees and airport lounge access for $95 a year. If you travel very frequently, the Citi Prestige earns 3 miles per dollar on travel, comes with Priority Pass lounge access, and a complimentary 4th night at hotels — that one is $495 annually. Would either of these interest you?

### Turn 4
**Customer:** The PremierMiles sounds good. Am I eligible?
**Bot:** Let me check the eligibility requirements.

> **State:** FAQLookup/Searching
> **FAQ Search:** "PremierMiles eligibility" → confidence = 0.72 → **BLENDED**
> **FAQ Base:** "PremierMiles requires minimum annual income of $30,000, minimum age 21, good credit standing."
> **G4 Hedge Enforcer:** HEDGED flag injected — medium confidence
> **LLM Pass 2:** Reasons on top of FAQ base, uses hedging language

**Bot:** The PremierMiles typically requires a minimum annual income of $30,000, you need to be at least 21, and have good credit standing. Based on your account history with us, you generally appear to be in good shape, though final approval depends on the full application review. Would you like to know what documents you'd need?

> **Note:** "typically", "generally" — hedge language enforced by G4

### Turn 5
**Customer:** Yes, what do I need to prepare?
**Bot:** Sure, let me get that list for you.

> **FAQ Search:** "PremierMiles required documents" → confidence = 0.93 → **PURE FAQ**
> **FAQ Result:** "Government-issued photo ID (passport or driver's license), proof of income (last 2 pay stubs or tax return), proof of address (utility bill or bank statement within 60 days), Social Security Number."

**Bot:** You'll need four things: a government-issued photo ID like your passport or driver's license, proof of income — your last two pay stubs or most recent tax return, a proof of address such as a utility bill or bank statement from the past 60 days, and your Social Security Number. Do you have those ready, or would you like to start the application now and upload later?

### Turn 6
**Customer:** Can I use my bank statements instead of pay stubs? I'm a freelancer.
**Bot:** Good question.

> **FAQ Search:** "alternative income proof freelancer credit card" → confidence = 0.54 → **PURE LLM**
> **LLM Pass 2:** Generates freely with disclaimer

**Bot:** For freelancers, bank statements showing regular income deposits are commonly accepted as an alternative. You could also provide your most recent tax return or 1099 forms. That said, I'd recommend confirming with the application team exactly which combination they'd prefer for your situation. Would you like to go ahead and start the application?

> **Note:** Pure LLM mode — includes "I'd recommend confirming" as natural disclaimer

### Turn 7
**Customer:** Yes, let's do it.
**Bot:** Great! I'll start the application process for you.

> **State:** Listening → WorkflowActive/StepExec
> **LLM Pass 1:**
> ```json
> {
>   "resolved_query": "start credit card application PremierMiles",
>   "action_type": "workflow",
>   "workflow_trigger": {"flow": "credit_card_application", "params": {"card_type": "PremierMiles"}},
>   "filler": "Great! I'll start the application process for you.",
>   "emotion_read": "positive"
> }
> ```
> **Workflow Engine:** credit_card_application Step 1 of 4: Confirm personal details
> **Step Type:** needs_input

**Bot:** Let me walk you through it. First, I have your name as Priya Sharma and your address on file. Is that information still current?

### Turn 8
**Customer:** Actually, I moved last month. New address is 450 Park Avenue, Apt 12B, New York, NY 10022.
**Bot:** Got it, I've updated your address. Now, could you confirm your annual income and employment status?

> **Workflow Step 2:** Collect income + employment
> **Thread Tracker:** credit_card_application ACTIVE, slots filled: [name, address], slots needed: [income, employment_status]

### Turn 9
**Customer:** I'm self-employed, freelance software consultant. About $95,000 a year.
**Bot:** Perfect. Last step before I submit — could you confirm your Social Security Number? You can provide just the last four digits for now; the full number will be collected securely during the formal sign-off.

> **Workflow Step 3:** Collect SSN (last 4)
> **Slots filled:** [name, address, income=95000, employment=self_employed]

### Turn 10
**Customer:** Last four is 7829.
**Bot:** Thank you. Let me submit your application now.

> **Workflow Step 4:** Submit application (auto step)
> **Tool Call:** `submit_credit_application({card_type: "PremierMiles", applicant: "Priya Sharma", address: "450 Park Ave Apt 12B, NY 10022", income: 95000, employment: "self_employed", ssn_last4: "7829"})`
> **API Response:** `{application_id: "APP-2026-44891", status: "under_review", estimated_decision: "2-3 business days"}`
> **Fact Store Written:** application_id=APP-2026-44891, status=under_review @ turn10

**Bot:** Your application has been submitted successfully. Your reference number is APP-2026-44891. You should receive a decision within 2 to 3 business days by email. Is there anything else I can help you with?

### Turn 11
**Customer:** No, that's all. Thank you so much!
**Bot:** You're welcome, Ms. Sharma! Good luck with the application. Have a wonderful day!

> **State:** Farewell
> **Workflow:** credit_card_application COMPLETE
