from __future__ import annotations

import uuid
from typing import Any


_RATES: dict[str, float] = {
    "USD_GBP": 0.7892,
    "USD_EUR": 0.9210,
    "USD_JPY": 149.50,
    "USD_BDT": 119.85,
}


class MockTransferService:
    async def get_exchange_rate(
        self, from_currency: str, to_currency: str, amount: float
    ) -> dict[str, Any]:
        key = f"{from_currency}_{to_currency}"
        rate = _RATES.get(key, 1.0)
        converted = round(amount * rate, 2)
        return {
            "rate": rate,
            "converted": converted,
            "from_currency": from_currency,
            "to_currency": to_currency,
            "amount": amount,
            "rate_valid_for": "15 minutes",
            "fee_wire": 35.00,
            "fee_fx": 12.50,
        }

    async def initiate_transfer(self, **kwargs: Any) -> dict[str, Any]:
        amount = kwargs.get("amount_usd", 0)
        target = kwargs.get("target_currency", "USD")
        key = f"USD_{target}"
        rate = _RATES.get(key, 1.0)
        fee = 47.50
        return {
            "transfer_id": f"WIR-2026-{uuid.uuid4().int % 1000000:06d}",
            "status": "processing",
            "amount_debited": round(amount + fee, 2),
            "converted_amount": round(amount * rate, 2),
            "target_currency": target,
            "estimated_arrival": "2026-03-13",
        }
