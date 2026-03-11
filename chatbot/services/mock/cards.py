from __future__ import annotations

import uuid
from typing import Any


_CARD_DETAILS: dict[str, dict[str, Any]] = {
    "credit_card_ending_2277": {
        "card": "credit_card_ending_2277", "type": "credit",
        "apr_purchase": 19.99, "apr_cash_advance": 24.99,
        "credit_limit": 15000, "current_balance": 3841.20,
    },
    "visa_ending_4455": {
        "card": "visa_ending_4455", "type": "credit",
        "apr_purchase": 17.49, "apr_cash_advance": 23.99,
        "credit_limit": 25000, "current_balance": 6240.00,
    },
    "debit_ending_7821": {
        "card": "debit_ending_7821", "type": "debit",
        "linked_account": "checking_8912",
        "daily_limit": 5000, "current_balance": 28930.50,
    },
    "visa_ending_8832": {
        "card": "visa_ending_8832", "type": "credit",
        "apr_purchase": 18.24, "apr_cash_advance": 24.99,
        "credit_limit": 20000, "current_balance": 2150.80,
    },
    "debit_ending_3310": {
        "card": "debit_ending_3310", "type": "debit",
        "linked_account": "checking_6641",
        "daily_limit": 3000, "current_balance": 5220.30,
    },
}


class MockCardService:
    def __init__(self) -> None:
        self._blocked: set[str] = set()
        self._blocked_merchants: dict[str, set[str]] = {}

    async def block_card(self, card_id: str, reason: str) -> dict[str, Any]:
        self._blocked.add(card_id)
        block_id = f"BLK-{card_id.split('_')[-1]}-0311"
        return {
            "status": "blocked",
            "block_id": block_id,
            "blocked_at": "2026-03-11T10:32:00Z",
            "replacement_eligible": True,
        }

    async def order_replacement(self, card_id: str, shipping: str = "expedited") -> dict[str, Any]:
        new_suffix = str(uuid.uuid4().int)[:4]
        card_type = "visa" if "visa" in card_id else "debit"
        return {
            "old_card": card_id,
            "new_card": f"{card_type}_ending_{new_suffix}",
            "shipping": shipping,
            "eta": "2-3 business days",
            "temp_virtual_card": True,
        }

    async def get_details(self, card_id: str) -> dict[str, Any]:
        return _CARD_DETAILS.get(card_id, {"card": card_id, "error": "card not found"})

    async def block_merchant(self, card_id: str, merchant_id: str) -> dict[str, Any]:
        if card_id not in self._blocked_merchants:
            self._blocked_merchants[card_id] = set()
        self._blocked_merchants[card_id].add(merchant_id)
        return {"blocked": True, "merchant": merchant_id}

    async def file_dispute(self, **kwargs: Any) -> dict[str, Any]:
        total = kwargs.get("total_amount", 0)
        txn_ids = kwargs.get("transaction_ids", [])
        return {
            "dispute_id": f"DSP-2026-{uuid.uuid4().int % 100000:05d}",
            "status": "under_investigation",
            "provisional_credit": True,
            "credit_amount": total,
            "disputed_transactions": txn_ids,
            "estimated_resolution": "10 business days",
        }
