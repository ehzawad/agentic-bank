# Scenario 05: International Wire Transfer

Customer needs to send money internationally. Demonstrates workflow with multiple required fields, fee lookups, and compliance checks.

## Systems Exercised
- Auth Gate
- FAQ Engine (fees, processing times)
- Workflow Engine (international_transfer flow with many slots)
- Tool Executor (get_exchange_rate, initiate_transfer)
- Tool Call Validator G2 (parameter validation)
- Fact Store (exchange rate, fees, confirmation)
- Clarifying state (ambiguous input resolution)

---

## Conversation

### Turn 1
**Customer:** I need to send some money to my mother in London.
**Bot:** Of course, I can help you set up an international wire transfer. Let me verify your identity first. Could I have your phone number or account number?

> **State:** Greeting → Authenticating/CollectID

### Turn 2
**Customer:** 347-555-0286
**Bot:** Thank you, verifying now.

> **Tool Call:** `verify(phone="3475550286")`
> **API Response:** `{verified: true, name: "Ahmed Hassan", accounts: ["checking_5519", "savings_1102"], segment: "standard", tenure: "4yr"}`
> **Session Store:** Ahmed Hassan, standard, checking+savings, verified

**Bot:** Thank you, Mr. Hassan. I'd be happy to help you send money to London. How much would you like to send, and would you like to send it in US dollars or British pounds?

### Turn 3
**Customer:** Around $2,000. She needs it in pounds though.
**Bot:** Let me get the current exchange rate for you.

> **State:** ToolAction/Executing
> **Tool Call:** `get_exchange_rate(from="USD", to="GBP", amount=2000)`
> **API Response:** `{rate: 0.7892, converted: 1578.40, rate_valid_for: "15 minutes", fee_wire: 35.00, fee_fx: 12.50}`
> **Fact Store Written:** GBP rate=0.7892, converted=1578.40 GBP, fees=47.50 @ turn3

**Bot:** At the current rate, $2,000 would convert to approximately 1,578.40 British pounds. There's a $35 wire transfer fee plus a $12.50 currency conversion fee, so $47.50 in total fees. The exchange rate is locked for 15 minutes if you'd like to proceed. Shall I set this up?

### Turn 4
**Customer:** Yes. What information do you need from me?
**Bot:** I'll need your mother's banking details in the UK. Let me walk you through it step by step.

> **State:** Listening → WorkflowActive/WaitUser
> **Workflow:** international_transfer flow started
> **Thread Tracker:** international_transfer ACTIVE
> **Slots needed:** [recipient_name, recipient_bank, sort_code, account_number, recipient_address, purpose]

**Bot:** First, what's your mother's full name as it appears on her UK bank account?

### Turn 5
**Customer:** Fatima Hassan
**Bot:** Got it. And which bank does she use in the UK?

> **Slots filled:** [recipient_name=Fatima Hassan]

### Turn 6
**Customer:** Barclays, I think. Or maybe Lloyds. Let me check... it's Barclays.
**Bot:** Barclays, noted. Do you have her sort code and account number? The sort code is a 6-digit number, usually formatted like 20-45-67.

> **Slots filled:** [recipient_name, recipient_bank=Barclays]
> **Note:** LLM correctly resolved the customer's self-correction without needing clarification

### Turn 7
**Customer:** Sort code is 20-18-42 and account is 73901856.
**Bot:** Thank you. And her address in the UK?

> **Slots filled:** [recipient_name, recipient_bank, sort_code=201842, account_number=73901856]
> **G2 Validator:** sort_code format valid (6 digits), account_number format valid (8 digits) ✓

### Turn 8
**Customer:** 14 Kensington Road, London, W8 4PL.
**Bot:** Almost done. For compliance purposes, what's the reason for this transfer? For example: family support, gift, education, medical expenses.

> **Slots filled:** [recipient_name, recipient_bank, sort_code, account_number, recipient_address=14 Kensington Road London W8 4PL]
> **Note:** Compliance/regulatory requirement — purpose of transfer

### Turn 9
**Customer:** Family support. Monthly living expenses for my mother.
**Bot:** Thank you. Let me confirm everything before I submit.

> **All slots filled.** Workflow ready for confirmation step.

**Bot:** Here's the transfer summary:
- **From:** Your checking account (ending 5519)
- **To:** Fatima Hassan, Barclays, Sort: 20-18-42, Acct: 73901856
- **Address:** 14 Kensington Road, London, W8 4PL
- **Amount:** $2,000.00 USD → ~£1,578.40 GBP
- **Fees:** $47.50 (wire $35 + FX $12.50)
- **Total debit:** $2,047.50
- **Purpose:** Family support
- **Estimated arrival:** 1-2 business days

Does everything look correct?

### Turn 10
**Customer:** Yes, that's all correct. Send it.
**Bot:** Initiating the transfer now.

> **Workflow Step: Execute transfer (auto after confirmation)**
> **Tool Call:** `initiate_transfer({from_account: "checking_5519", recipient_name: "Fatima Hassan", recipient_bank: "Barclays", sort_code: "201842", account_number: "73901856", address: "14 Kensington Road London W8 4PL", amount_usd: 2000.00, target_currency: "GBP", purpose: "family_support"})`
> **API Response:** `{transfer_id: "WIR-2026-031108", status: "processing", amount_debited: 2047.50, gbp_amount: 1578.40, estimated_arrival: "2026-03-13"}`
> **Fact Store Written:** transfer_id=WIR-2026-031108, debited=2047.50, arrival=2026-03-13 @ turn10

**Bot:** Your transfer has been submitted successfully.
- **Reference:** WIR-2026-031108
- **Amount debited:** $2,047.50 from your checking account
- **Your mother will receive:** £1,578.40
- **Estimated arrival:** March 13, 2026

You'll receive a confirmation email and SMS shortly. Is there anything else I can help with?

### Turn 11
**Customer:** Can I set this up as a recurring monthly transfer?
**Bot:** Let me check that for you.

> **FAQ Search:** "recurring international wire transfer setup" → confidence = 0.74 → **BLENDED**
> **G4 Hedge Enforcer:** HEDGED flag

**Bot:** We do typically offer recurring international transfers. However, since exchange rates fluctuate, each monthly transfer would generally use the rate at the time of execution rather than today's rate. The $35 wire fee usually applies each time as well. Would you like me to set up an automatic monthly transfer of $2,000 to the same account?

### Turn 12
**Customer:** Hmm, let me think about the recurring part. The one-time transfer is fine for now. Thanks!
**Bot:** No problem, Mr. Hassan. The transfer to your mother is all set. If you decide on the recurring option later, just give us a call. Have a great day!

> **State:** Farewell
> **Workflow:** international_transfer COMPLETE
> **Thread Tracker:** recurring_transfer SUSPENDED (customer deferred)
