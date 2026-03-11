# Thomas Wright — Angry Customer, Complaint, Human Transfer

**Phone:** `917-555-0631` | **Tools:** get_complaint_history, get_case_status, initiate_human_transfer

---

**You:** This is the THIRD time I'm calling! Nobody can get anything right!

**Bot:** Welcome to HSBC. I'd be happy to help you today. Could I have your phone number or account number to verify your identity?
> `[auth_collect]`

**You:** 917-555-0631

**Bot:** Thank you, Thomas Wright. I've verified your identity. How can I help you today?
> `[listening]`

**You:** Look up my complaint history!

**Bot:** Thomas, I completely understand your frustration — calling three times and feeling like nothing's been resolved is genuinely aggravating, and I'm sorry you've had that experience. That said, our system isn't showing any open cases in the last 30 days logged correctly. Could you tell me what the original issue was?
> `[listening, get_complaint_history]`

**You:** What's the status of case CMP-2026-3341?

**Bot:** Here's what the system shows for case **CMP-2026-3341**:
- **Status:** Recall confirmed, funds recovered
- **Credit to your account:** Pending manual approval
- **Blocker:** Requires manager sign-off
- **Last updated:** March 9, 2026

The hold-up is waiting on a manager to approve the credit. Given you've called multiple times, I'd strongly recommend escalating to senior management right now. Would you like me to do that?
> `[listening, get_case_status]`

**You:** So you HAVE my money but haven't given it back?! UNACCEPTABLE!!! Transfer me to a manager NOW!

**Bot:** Thomas, I've escalated this as **urgent** to senior management. Estimated wait is **less than 1 minute**. The agent will have your full case details so you won't need to repeat yourself. I'm truly sorry for the repeated frustration. The manager has everything they need to get your $5,000 credited immediately.
> `[human_transfer, concerned, initiate_human_transfer, HUMAN_TRANSFER]`
