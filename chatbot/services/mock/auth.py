from __future__ import annotations

from typing import Any


# Customer database matching the 10 scenarios
_CUSTOMERS: dict[str, dict[str, Any]] = {
    "9175550142": {
        "name": "James Chen", "customer_id": "james_chen_4821",
        "accounts": ["checking_4821", "savings_7903"], "cards": [],
        "segment": "premier", "tenure": "5yr",
    },
    "2125550198": {
        "name": "Priya Sharma", "customer_id": "priya_sharma_3301",
        "accounts": ["savings_3301"], "cards": [],
        "segment": "standard", "tenure": "2yr",
        "credit_score_band": "good",
    },
    "6465550317": {
        "name": "David Okonkwo", "customer_id": "david_okonkwo_8912",
        "accounts": ["checking_8912"],
        "cards": ["visa_ending_4455", "debit_ending_7821"],
        "segment": "citigold", "tenure": "8yr",
    },
    "3475550286": {
        "name": "Ahmed Hassan", "customer_id": "ahmed_hassan_5519",
        "accounts": ["checking_5519", "savings_1102"], "cards": [],
        "segment": "standard", "tenure": "4yr",
    },
    "4155550193": {
        "name": "Sarah Kim", "customer_id": "sarah_kim_6641",
        "accounts": ["checking_6641"],
        "cards": ["visa_ending_8832", "debit_ending_3310"],
        "segment": "preferred", "tenure": "6yr",
    },
    "7185550412": {
        "name": "Robert & Lisa Chen", "customer_id": "robert_chen_4402",
        "accounts": ["joint_checking_4402", "joint_savings_9918"], "cards": [],
        "segment": "premier", "tenure": "7yr",
        "existing_mortgage": False,
    },
    "3125550847": {
        "name": "Elena Volkova", "customer_id": "elena_volkova_2291",
        "accounts": ["checking_2291", "savings_7740"], "cards": [],
        "segment": "standard", "tenure": "3yr",
    },
    "9175550631": {
        "name": "Thomas Wright", "customer_id": "thomas_wright_1198",
        "accounts": ["checking_1198"], "cards": [],
        "segment": "citigold", "tenure": "12yr",
        "vip_flag": True,
    },
    "6465550921": {
        "name": "Jennifer Park", "customer_id": "jennifer_park_3301",
        "accounts": ["checking_3301", "savings_8850"],
        "cards": ["credit_card_ending_2277"],
        "segment": "preferred", "tenure": "5yr",
    },
}

# Also support account-number lookups
_ACCOUNT_MAP: dict[str, str] = {
    "88342210": "3125550847_alt",  # Scenario 04 — Maria Santos
}
_CUSTOMERS["3125550847_alt"] = {
    "name": "Maria Santos", "customer_id": "maria_santos_8834",
    "accounts": ["checking_8834", "savings_2210"], "cards": [],
    "segment": "advance", "tenure": "3yr",
    "credit_score_band": "excellent",
}


class MockAuthService:
    async def verify(self, identifier: str, **kwargs: Any) -> dict[str, Any]:
        # Strip non-digit for phone lookup
        clean = "".join(c for c in identifier if c.isdigit())

        # Try direct phone lookup
        customer = _CUSTOMERS.get(clean)

        # Try account number lookup
        if customer is None and clean in _ACCOUNT_MAP:
            customer = _CUSTOMERS.get(_ACCOUNT_MAP[clean])

        if customer is None:
            return {"verified": False}

        return {"verified": True, **customer}
