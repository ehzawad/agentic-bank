# Scenario 06: Lost Card — Temporary Block, Replacement & PIN Reset

Customer lost their wallet and needs immediate card protection, replacement, and PIN management. Demonstrates urgent workflow with parallel tool calls.

## Systems Exercised
- Auth Gate (alternative verification — no card in hand)
- Tool Executor (parallel: block_card + check_recent_activity)
- Workflow Engine (lost_card_replacement flow)
- FAQ Engine (PIN reset process, delivery times)
- Emotion Tracker (panicked → calmed)
- Proactive actions (bot-initiated security steps)

---

## Conversation

### Turn 1
**Customer:** I lost my wallet! I need to freeze my cards right away!
**Bot:** I'm on it. Let me secure your accounts immediately. Since you don't have your card, can you verify with your phone number and date of birth?

> **State:** Greeting → Authenticating/CollectID
> **Emotion Tracker:** panicked
> **Note:** Bot adapts verification method — wallet lost means no card number available

### Turn 2
**Customer:** 415-555-0193, and my birthday is March 15, 1988.
**Bot:** Verifying now.

> **Tool Call:** `verify(phone="4155550193", dob="1988-03-15")`
> **API Response:** `{verified: true, name: "Sarah Kim", accounts: ["checking_6641"], cards: ["visa_ending_8832", "debit_ending_3310"], segment: "preferred", tenure: "6yr"}`
> **Session Store:** Sarah Kim, preferred, 2 cards: visa_8832 + debit_3310

**Bot:** Ms. Kim, I've confirmed your identity. I can see you have two cards — a Visa credit card ending in 8832 and a debit card ending in 3310. Let me block both right now and check for any suspicious activity.

> **Proactive:** Bot blocks both cards without waiting to be asked — context makes intent clear

### Turn 3
**Customer:** Yes, block everything!
**Bot:** Blocking both cards and checking recent activity now.

> **State:** ToolAction/Executing
> **Parallel Tool Calls:**
> ```json
> [
>   {"function": "block_card", "params": {"card": "visa_8832", "reason": "lost_wallet"}},
>   {"function": "block_card", "params": {"card": "debit_3310", "reason": "lost_wallet"}},
>   {"function": "get_transactions", "params": {"card": "visa_8832", "date": "2026-03-11", "hours": 24}},
>   {"function": "get_transactions", "params": {"card": "debit_3310", "date": "2026-03-11", "hours": 24}}
> ]
> ```
> **Results:**
> - visa_8832: BLOCKED, block_id=BLK-8832-0311
> - debit_3310: BLOCKED, block_id=BLK-3310-0311
> - visa_8832 transactions (last 24h): $45.20 at Whole Foods (yesterday), $12.00 at Uber (yesterday)
> - debit_3310 transactions (last 24h): $3.50 ATM balance inquiry (today, 9:15 AM)
> **Fact Store Written:** both cards blocked, last 24h transactions logged @ turn3

**Bot:** Both cards are now blocked. Here's what I found in the last 24 hours:
- **Visa 8832:** $45.20 at Whole Foods yesterday, $12.00 Uber ride yesterday
- **Debit 3310:** $3.50 ATM balance inquiry today at 9:15 AM

Do all of those look familiar, or is anything suspicious?

### Turn 4
**Customer:** Those are all mine. I think I lost my wallet at lunch today, so nothing should be wrong yet.
**Bot:** Good — no unauthorized charges. Your cards are secured. Would you like me to order replacements for both?

> **Emotion Tracker:** panicked → calming (situation under control)
> **Thread Tracker:** lost_card ACTIVE, slots filled: [both_blocked, no_fraud], next: replacement decision

### Turn 5
**Customer:** Yes please. How long will that take?
**Bot:** Let me order those and check the delivery timeline.

> **Workflow:** lost_card_replacement Step: order replacements
> **Tool Call:** `order_replacement_card(cards=["visa_8832", "debit_3310"], shipping="expedited")`
> **API Response:**
> ```json
> {
>   "replacements": [
>     {"old": "visa_8832", "new": "visa_ending_1197", "shipping": "expedited", "eta": "2-3 business days"},
>     {"old": "debit_3310", "new": "debit_ending_5504", "shipping": "expedited", "eta": "2-3 business days"}
>   ],
>   "temp_virtual_card": {"debit": true, "credit": true}
> }
> ```
> **FAQ Search:** "replacement card expedited delivery" → confidence = 0.91 → **PURE FAQ**

**Bot:** Both replacement cards are ordered with expedited delivery:
- **New Visa:** ending in 1197, arriving in 2-3 business days
- **New Debit:** ending in 5504, arriving in 2-3 business days

In the meantime, I've activated temporary virtual card numbers for both — you can find them in your mobile banking app right away. They work for online and contactless payments.

### Turn 6
**Customer:** Oh that's great about the virtual cards. What about my PIN? Will it be the same?
**Bot:** Let me check.

> **FAQ Search:** "replacement card PIN same or new" → confidence = 0.87 → **PURE FAQ**
> **FAQ Result:** "Replacement cards are issued with a new PIN. Mailed separately for security. Can also set PIN via mobile app or ATM on first use."

**Bot:** Your replacement cards will come with new PINs, mailed separately from the cards for security. However, once you receive the new cards, you can set your own PIN immediately through the mobile app or at any HSBC ATM on first use. Would you like help with anything else?

### Turn 7
**Customer:** Actually, should I also update my card on file for my subscriptions? Like Netflix and stuff?
**Bot:** Yes, good thinking.

> **FAQ Search:** "update card on file subscriptions after replacement" → confidence = 0.78 → **BLENDED**
> **G4 Hedge Enforcer:** HEDGED flag

**Bot:** Yes, you'll want to update any recurring charges. Your new card numbers are different, so subscriptions like Netflix, Spotify, utilities, and any auto-pay bills will typically need to be updated once you receive the new cards. Some merchants may automatically update through the card network, but it's generally best not to rely on that. You can use the virtual card numbers in the mobile app to update your most urgent subscriptions right away.

### Turn 8
**Customer:** Got it. I think that covers everything. Thank you so much for being so quick about this!
**Bot:** Of course, Ms. Kim. I'm glad we could secure everything quickly. Just to recap: both cards are blocked, replacements are on the way, and you have virtual cards available now. If you notice any suspicious activity at all, call us right away. Take care!

> **State:** Farewell
> **Workflow:** lost_card_replacement COMPLETE
> **Emotion Tracker:** panicked → calming → relieved
