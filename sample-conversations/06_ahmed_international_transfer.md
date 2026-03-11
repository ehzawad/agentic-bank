# Ahmed Hassan — International Wire Transfer

**Phone:** `347-555-0286` | **Tools:** get_exchange_rate, get_balance, initiate_transfer

---

**You:** I need to send money to my mother in London

**Bot:** Welcome to HSBC. I'd be happy to help you today. Could I have your phone number or account number to verify your identity?
> `[auth_collect]`

**You:** 347-555-0286

**Bot:** Thank you, Ahmed Hassan. I've verified your identity. How can I help you today?
> `[listening]`

**You:** How much would $2,000 be in British pounds?

**Bot:** Here's the current exchange rate breakdown:
- **Converted amount:** £1,578.40 GBP
- **Exchange rate:** 0.7892 (valid for 15 minutes)
- **Wire transfer fee:** $35.00
- **FX fee:** $12.50

Would you like to proceed with sending this?
> `[listening, get_exchange_rate]`

**You:** What's my checking balance?

**Bot:** Your checking account currently has **$8,750.00**. Your balance is sufficient to cover the transfer and fees. Would you like to initiate the wire? I'll need your mother's banking details.
> `[listening, get_balance]`

**You:** Send the transfer. Recipient: Fatima Hassan, Barclays, sort code 20-18-42, account 73901856, 14 Kensington Road London W8 4PL. Family support.

**Bot:** Your transfer has been initiated:
- **Transfer ID:** WIR-2026-939847
- **Amount Debited:** $2,047.50 (includes $47.50 in fees)
- **Amount Received:** £1,578.40 GBP
- **Estimated Arrival:** March 13, 2026
> `[listening, initiate_transfer]`

**You:** Thanks bye!

**Bot:** Transfer confirmed! Summary: $2,047.50 debited, £1,578.40 sent to Fatima Hassan at Barclays, arriving March 13. Take care, Ahmed!
> `[farewell]`
