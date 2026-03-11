# Priya Sharma — FAQ Deep Dive, All 3 Confidence Tiers

**Phone:** `212-555-0198` | **Tools:** search_knowledge_base

---

**You:** Hello

**Bot:** Welcome to HSBC. I'd be happy to help you today. Could I have your phone number or account number to verify your identity?
> `[auth_collect]`

**You:** 212-555-0198

**Bot:** Thank you, Priya Sharma. I've verified your identity. How can I help you today?
> `[listening]`

**You:** What are the eligibility requirements for a credit card?

**Bot:** To be eligible for an HSBC credit card, you would typically need:
- **Age:** At least 21 years old
- **Income:** Minimum annual income of $30,000
- **Credit:** Good credit standing
- **Banking history:** At least 6 months

As a 2-year customer with a good credit score, you look well-positioned! I'd recommend confirming exact requirements with a specialist as specific cards may vary.
> `[listening, search_knowledge_base]` — **HIGH confidence, direct answer**

**You:** What's the difference between a fixed rate mortgage and an adjustable rate?

**Bot:** Here's a general overview:
- **Fixed Rate:** Interest locked for the entire term — consistent, predictable payments
- **ARM (7/1):** Fixed for 7 years, then adjusts annually. Caps *generally* around 2% per adjustment, 5% lifetime

If you value stability and plan to stay long-term, a fixed rate is *typically* the safer choice. I'd *recommend speaking with a mortgage specialist* for tailored advice.
> `[listening, search_knowledge_base]` — **MEDIUM confidence, hedged language ("generally", "typically")**

**You:** Should I invest in cryptocurrency?

**Bot:** Investment advice — especially around cryptocurrency — falls outside my scope as a banking assistant. For personalised investment guidance, I'd recommend speaking with a **qualified financial advisor** or visiting your nearest branch where a specialist may be able to help.
> `[listening]` — **LOW confidence, disclaimer + redirect to specialist**
