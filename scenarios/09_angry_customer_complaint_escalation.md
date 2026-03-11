# Scenario 09: Angry Customer — Complaint Escalation Path

Customer is furious about repeated service failures. Demonstrates the full emotion escalation pipeline, empathy responses, and human transfer.

## Systems Exercised
- Auth Gate
- Emotion Tracker (frustrated → angry → furious — 3+ turn trajectory)
- Emotion Escalation G5 (proactive human transfer offer)
- Tool Executor (get_complaint_history, get_case_status)
- Talk mode (empathy, acknowledgment)
- State Machine: Listening → HumanTransfer
- Thread Tracker (complaint tracking)

---

## Conversation

### Turn 1
**Customer:** This is the THIRD time I'm calling about this! Nobody at this bank can get anything right!
**Bot:** I'm very sorry you've had to call multiple times, and I understand how frustrating that must be. Let me look into this personally and try to get it resolved right now. Could I have your phone number so I can pull up your case?

> **State:** Greeting → Authenticating/CollectID
> **Emotion Tracker:** angry (high initial reading — caps, "third time", frustration language)
> **LLM Pass 1:** emotion_read: angry, talk_type: empathy
> **Note:** Bot leads with empathy, acknowledges frustration before asking for verification

### Turn 2
**Customer:** 917-555-0631. My name is Thomas Wright. And before you ask, YES I've already verified my identity twice today.
**Bot:** I completely understand, Mr. Wright. Let me verify quickly — I'll pull everything up so you don't have to repeat yourself.

> **Tool Call:** `verify(phone="9175550631")`
> **API Response:** `{verified: true, name: "Thomas Wright", accounts: ["checking_1198"], segment: "citigold", tenure: "12yr", vip_flag: true}`
> **Session Store:** Thomas Wright, Citigold, 12yr tenure, VIP

> **Tool Call:** `get_complaint_history(customer_id="thomas_wright_1198")`
> **API Response:**
> ```json
> {
>   "open_cases": [
>     {
>       "case_id": "CMP-2026-3341",
>       "subject": "Wire transfer to wrong account",
>       "opened": "2026-02-25",
>       "status": "pending_review",
>       "last_agent": "Agent_44",
>       "notes": "Customer reported $5,000 wire sent to wrong account. Recall initiated but not confirmed. Customer called back 2x, no resolution communicated."
>     }
>   ],
>   "interaction_count_30d": 5
> }
> ```
> **Fact Store Written:** case CMP-2026-3341, wire recall pending, 5 interactions in 30 days @ turn2

**Bot:** Mr. Wright, I can see your open case — CMP-2026-3341 regarding the $5,000 wire transfer that went to the wrong account. It was opened on February 25th and I can see you've called several times since then. Let me check the current status right now.

> **Note:** Bot immediately shows it has context — customer doesn't need to re-explain

### Turn 3
**Customer:** It's been TWO WEEKS! Five thousand dollars of MY money sent to the wrong place and nobody can tell me what's happening!
**Bot:** You're absolutely right — two weeks without a clear answer on $5,000 is unacceptable, and I apologize for that. Let me get you the latest status this second.

> **Emotion Tracker:** angry → furious (escalating — caps, exclamation, specific complaint about duration)
> **LLM Pass 1:** emotion_read: furious, trajectory: angry → furious (2 turns)

> **Tool Call:** `get_case_status(case_id="CMP-2026-3341")`
> **API Response:**
> ```json
> {
>   "case_id": "CMP-2026-3341",
>   "status": "recall_confirmed",
>   "recall_status": "funds_recovered",
>   "recovered_amount": 5000.00,
>   "credit_to_account": "pending_manual_approval",
>   "blocker": "requires_manager_sign_off",
>   "last_updated": "2026-03-09"
> }
> ```
> **Fact Store Written:** recall confirmed, funds recovered, pending manager sign-off @ turn3

**Bot:** Mr. Wright, I have an update. The wire recall was actually successful — the $5,000 has been recovered. The issue is that crediting it back to your account requires a manager's sign-off, and that step appears to have stalled since March 9th. I can see why no one communicated this to you, and that's a failure on our part. I'm genuinely sorry.

### Turn 4
**Customer:** So you HAVE my money but you just haven't given it back?! That's even worse! I've been a customer for 12 years and this is how I'm treated?
**Bot:** You're right to be upset, Mr. Wright, and I hear you. Twelve years of loyalty deserves far better than this.

> **Emotion Tracker:** furious → furious (sustained high anger, 3+ turns)
> **G5 Emotion Escalation TRIGGERED:** Rising emotion over 3+ turns, anger trajectory sustained at maximum
> **Action:** Proactively offer human transfer + escalation

**Bot:** Here's what I'd like to do right now. I want to connect you directly with a senior manager who has the authority to approve this credit to your account immediately. Given your Citigold status and how long this has taken, this should have been escalated days ago. Would you like me to transfer you to a senior manager right now, or would you prefer I formally escalate the case and have them call you within the hour?

> **Note:** G5 triggered proactive human transfer. Bot doesn't just offer — it explains WHY and gives options for how

### Turn 5
**Customer:** Transfer me now. And I want this officially documented as a formal complaint.
**Bot:** Absolutely. Let me file the formal complaint and transfer you.

> **State:** Listening → HumanTransfer
> **Tool Call:** `file_formal_complaint({customer_id: "thomas_wright_1198", related_case: "CMP-2026-3341", complaint: "Two-week delay in crediting recovered wire transfer funds, lack of communication, required 5 calls", priority: "urgent", customer_segment: "citigold_vip"})`
> **API Response:** `{complaint_id: "FML-2026-0892", priority: "urgent", assigned_to: "Senior Manager - Client Relations", status: "open"}`
> **Fact Store Written:** formal complaint FML-2026-0892, urgent priority @ turn5

> **Tool Call:** `initiate_transfer(type="human_agent", priority="urgent", department="senior_management", context={case_id: "CMP-2026-3341", complaint_id: "FML-2026-0892", customer_emotion: "furious", summary: "Recovered $5K wire not credited, 2 weeks, 5 calls, Citigold 12yr customer"})`

**Bot:** Mr. Wright, I've filed your formal complaint — your reference number is FML-2026-0892, marked as urgent priority. I'm transferring you now to a senior manager in Client Relations. I've included the full context of your case so you won't have to explain everything again. They'll have your case, the recovery details, and the credit approval all in front of them.

I'm sorry again for this experience. The manager should be able to resolve the credit immediately.

> **State:** HumanTransfer
> **Full context package sent to human agent:**
> - Session: Citigold, 12yr, VIP
> - Case history: CMP-2026-3341
> - Complaint: FML-2026-0892
> - Emotion trajectory: angry → furious (sustained)
> - Key fact: $5K recovered, pending manager sign-off
> - Customer expectation: immediate credit

### Turn 6
**Customer:** Fine. Thank you for actually looking into it at least.
**Bot:** Of course, Mr. Wright. I'm sorry it took this long to get answers. The manager will take it from here. I hope we can make this right for you today.

> **Handoff complete**
> **All memory stores updated with full interaction record**
