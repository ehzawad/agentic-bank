from __future__ import annotations

import math
from typing import Any


class MockLoanService:
    async def check_eligibility(
        self, customer_id: str, amount: float, purpose: str
    ) -> dict[str, Any]:
        # Simulate eligibility based on amount
        max_approved = min(amount * 1.2, 50000)
        rate = 7.49 if amount <= 30000 else 8.99
        return {
            "eligible": True,
            "approved_amount": max_approved,
            "offered_rate": rate,
            "term_options": [24, 36, 48, 60],
        }

    async def calculate_emi(
        self, amount: float, rate: float, terms: list[int]
    ) -> dict[str, Any]:
        monthly_rate = rate / 100 / 12
        result: dict[str, Any] = {}
        for term in terms:
            if monthly_rate == 0:
                emi = amount / term
            else:
                emi = amount * monthly_rate * math.pow(1 + monthly_rate, term) / (
                    math.pow(1 + monthly_rate, term) - 1
                )
            total_interest = (emi * term) - amount
            result[f"emi_{term}mo"] = round(emi, 2)
            result[f"total_interest_{term}mo"] = round(total_interest, 2)
        return result

    async def check_mortgage_eligibility(self, **kwargs: Any) -> dict[str, Any]:
        down_payment = kwargs.get("down_payment", 0)
        price_range = kwargs.get("home_price_range", [500000, 600000])
        max_price = min(price_range[1], 620000)
        dp_pct = (down_payment / max_price * 100) if max_price else 0
        return {
            "eligible": True,
            "max_approved": max_price,
            "down_payment_pct_at_max": round(dp_pct, 2),
            "rates": {
                "30yr_fixed": 6.375,
                "15yr_fixed": 5.750,
                "7_1_arm": 5.500,
            },
            "estimated_monthly": {
                "30yr_at_low": {
                    "principal_interest": 2621, "tax_insurance": 650, "total": 3271
                },
                "30yr_at_high": {
                    "principal_interest": 3057, "tax_insurance": 730, "total": 3787
                },
            },
        }
