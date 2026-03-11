# Scenario 08: Account Statement & Tax Document Request

Customer needs account statements for a visa application and tax documents for filing. Demonstrates document generation tools and FAQ for process questions.

## Systems Exercised
- Auth Gate
- Tool Executor (generate_statement, get_tax_document)
- FAQ Engine (document turnaround, tax form types)
- Workflow Engine (simple 2-step document request)
- Thread Tracker (two related sub-topics)
- Fact Store (document references)

---

## Conversation

### Turn 1
**Customer:** Hi, I need my account statements. I'm applying for a travel visa and the embassy wants to see my bank records.
**Bot:** Hello! I can help you get those statements. Let me verify your identity first. Could I have your phone number or account number?

> **State:** Greeting → Authenticating/CollectID

### Turn 2
**Customer:** 312-555-0847
**Bot:** Thank you, one moment.

> **Tool Call:** `verify(phone="3125550847")`
> **API Response:** `{verified: true, name: "Elena Volkova", accounts: ["checking_2291", "savings_7740"], segment: "standard", tenure: "3yr"}`
> **Session Store:** Elena Volkova, standard, checking+savings, 3yr

**Bot:** Thank you, Ms. Volkova. Which account statements do you need — checking, savings, or both? And how many months does the embassy require?

### Turn 3
**Customer:** They want 6 months for both accounts.
**Bot:** Got it. Let me generate those for you.

> **State:** ToolAction/Executing
> **LLM Pass 1:**
> ```json
> {
>   "resolved_query": "generate 6-month statements for both checking and savings accounts for visa application",
>   "action_type": "tool_call",
>   "tool_call": [
>     {"function": "generate_statement", "params": {"account": "checking_2291", "months": 6, "format": "pdf", "purpose": "visa_application"}},
>     {"function": "generate_statement", "params": {"account": "savings_7740", "months": 6, "format": "pdf", "purpose": "visa_application"}}
>   ],
>   "filler": "Got it. Let me generate those for you.",
>   "emotion_read": "neutral"
> }
> ```
> **Parallel tool results:**
> - checking_2291: `{statement_id: "STM-2291-6M", period: "Sep 2025 - Mar 2026", pages: 12, download_url: "/statements/STM-2291-6M.pdf", stamped: true}`
> - savings_7740: `{statement_id: "STM-7740-6M", period: "Sep 2025 - Mar 2026", pages: 4, download_url: "/statements/STM-7740-6M.pdf", stamped: true}`
> **Fact Store Written:** STM-2291-6M and STM-7740-6M generated @ turn3

**Bot:** Both statements are ready:
- **Checking (ending 2291):** September 2025 through March 2026, 12 pages, bank-stamped
- **Savings (ending 7740):** Same period, 4 pages, bank-stamped

Both are available as PDFs in your online banking under "Statements & Documents." They include the bank's official stamp, which most embassies accept. Would you like me to also email them to your address on file?

### Turn 4
**Customer:** Yes, please email them. Also, does it have the bank letterhead and everything? The embassy is very particular about format.
**Bot:** Sending them now.

> **Tool Call:** `email_document(documents=["STM-2291-6M", "STM-7740-6M"], email="elena.v@email.com")`
> **API Response:** `{sent: true, to: "elena.v@email.com"}`

> **FAQ Search:** "official bank statement format embassy visa letterhead" → confidence = 0.86 → **PURE FAQ**
> **FAQ Result:** "Official statements include: bank letterhead, account holder name, account number (partially masked), transaction details, running balance, bank stamp, and branch address. Accepted by most embassies. If embassy requires notarized copy, visit any branch."

**Bot:** Emailed to elena.v@email.com. And yes, our official statements include full bank letterhead, your name, masked account number, all transactions with running balances, the bank's official stamp, and our branch address. Most embassies accept this format. If your embassy specifically requires a notarized or signed copy, you'd need to visit any branch — they can stamp and sign it on the spot, usually within 15 minutes.

### Turn 5
**Customer:** Good to know. While I'm at it, can I also get my tax documents? I need to file my taxes and I think the bank sends some form for the interest I earned.
**Bot:** Of course. Let me pull your tax documents.

> **State:** ToolAction/Executing
> **Thread Tracker:** statement_request RESOLVED, tax_document_request ACTIVE
> **FAQ Search (quick):** "bank tax document interest earned" → confidence = 0.90 → **PURE FAQ**

> **Tool Call:** `get_tax_document(customer_id="elena_volkova_2291", tax_year=2025, doc_type="1099-INT")`
> **API Response:** `{document_id: "TAX-1099INT-2025-2291", tax_year: 2025, interest_earned: 847.32, available: true, download_url: "/tax/TAX-1099INT-2025.pdf"}`
> **Fact Store Written:** 1099-INT for 2025, interest=$847.32 @ turn5

**Bot:** Your 1099-INT form for tax year 2025 is ready. It shows $847.32 in interest earned across your accounts. It's already available in your online banking under "Tax Documents," and I'll email it along with the statements. Is that the only tax form you need?

### Turn 6
**Customer:** That should be it. I didn't have any other investment accounts or anything. Actually wait — do I need to report the interest if it's under $1,000?
**Bot:** Good question.

> **FAQ Search:** "do I need to report bank interest under 1000 taxes" → confidence = 0.48 → **PURE LLM**
> **LLM Pass 2:** Generates freely with disclaimer

**Bot:** Technically, all interest income is reportable to the IRS regardless of the amount — the $847.32 should be included on your tax return. That said, I'm not a tax advisor, and your specific tax situation may have nuances. I'd recommend checking with a tax professional or the IRS guidelines to make sure you're filing correctly.

> **Note:** Pure LLM mode — tax advice is outside banking FAQ scope, appropriate disclaimer added

### Turn 7
**Customer:** Makes sense. Thanks for all the help!
**Bot:** You're welcome, Ms. Volkova! To recap, I've sent your 6-month statements for both accounts and your 1099-INT form to your email. Good luck with the visa application and tax filing!

> **State:** Farewell
> **All memory stores updated**
