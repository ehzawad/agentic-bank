from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


_BALANCES: dict[str, dict[str, Any]] = {
    "checking_4821": {"balance": 12450.75, "currency": "USD"},
    "savings_7903": {"balance": 34200.00, "currency": "USD"},
    "savings_3301": {"balance": 18750.00, "currency": "USD"},
    "checking_8912": {"balance": 28930.50, "currency": "USD"},
    "checking_5519": {"balance": 8750.00, "currency": "USD"},
    "savings_1102": {"balance": 15400.00, "currency": "USD"},
    "checking_6641": {"balance": 5220.30, "currency": "USD"},
    "joint_checking_4402": {"balance": 42100.00, "currency": "USD"},
    "joint_savings_9918": {"balance": 130000.00, "currency": "USD"},
    "checking_2291": {"balance": 7830.45, "currency": "USD"},
    "savings_7740": {"balance": 22140.00, "currency": "USD"},
    "checking_1198": {"balance": 67500.00, "currency": "USD"},
    "checking_3301": {"balance": 4215.60, "currency": "USD"},
    "savings_8850": {"balance": 22140.00, "currency": "USD"},
    "checking_8834": {"balance": 19340.00, "currency": "USD"},
    "savings_2210": {"balance": 45000.00, "currency": "USD"},
}

_TRANSACTIONS: dict[str, list[dict[str, Any]]] = {
    "checking_4821": [
        {"id": "TXN-90812", "date": "2026-03-10", "amount": -89.99,
         "merchant": "AMZN Digital*RT4K92", "category": "digital_services",
         "description": "Amazon Prime + Add-on subscription renewal"},
        {"id": "TXN-90750", "date": "2026-03-09", "amount": -42.30,
         "merchant": "WHOLE FOODS #1022", "category": "groceries"},
    ],
    "visa_ending_4455": [
        {"id": "TXN-71001", "date": "2026-03-11", "time": "06:12", "amount": -249.99,
         "merchant": "BESTBUY.COM", "location": "online", "category": "electronics"},
        {"id": "TXN-71002", "date": "2026-03-11", "time": "06:45", "amount": -189.50,
         "merchant": "NIKE STORE #892", "location": "Chicago, IL", "category": "retail"},
        {"id": "TXN-71003", "date": "2026-03-11", "time": "07:30", "amount": -420.00,
         "merchant": "ELECTRONICS HUB", "location": "Chicago, IL", "category": "electronics"},
        {"id": "TXN-71004", "date": "2026-03-11", "time": "08:15", "amount": -34.50,
         "merchant": "STARBUCKS #1204", "location": "New York, NY", "category": "food"},
    ],
    "visa_ending_8832": [
        {"id": "TXN-60201", "date": "2026-03-10", "amount": -45.20,
         "merchant": "WHOLE FOODS #890", "category": "groceries"},
        {"id": "TXN-60199", "date": "2026-03-10", "amount": -12.00,
         "merchant": "UBER *TRIP", "category": "transport"},
    ],
    "debit_ending_3310": [
        {"id": "TXN-60300", "date": "2026-03-11", "time": "09:15", "amount": -3.50,
         "merchant": "ATM BALANCE INQUIRY", "category": "atm"},
    ],
    "credit_card_ending_2277": [
        {"id": "TXN-55091", "date": "2026-03-08", "amount": -156.80,
         "merchant": "DGTL MKTPLC*SRV", "category": "digital_services"},
        {"id": "TXN-54220", "date": "2026-02-15", "amount": -156.80,
         "merchant": "DGTL MKTPLC*SRV", "category": "digital_services"},
        {"id": "TXN-54100", "date": "2026-02-10", "amount": -230.00,
         "merchant": "NORDSTROM #442", "category": "retail"},
    ],
    # Additional accounts with realistic transaction data
    "checking_5519": [
        {"id": "TXN-80101", "date": "2026-03-10", "amount": -75.00,
         "merchant": "VERIZON WIRELESS", "category": "utilities"},
        {"id": "TXN-80099", "date": "2026-03-08", "amount": -32.50,
         "merchant": "UBER EATS", "category": "food"},
    ],
    "savings_3301": [
        {"id": "TXN-70010", "date": "2026-03-01", "amount": 2500.00,
         "merchant": "PAYROLL DEPOSIT", "category": "income"},
    ],
    "checking_8912": [
        {"id": "TXN-81001", "date": "2026-03-10", "amount": -120.00,
         "merchant": "CON EDISON", "category": "utilities"},
        {"id": "TXN-81002", "date": "2026-03-09", "amount": -65.40,
         "merchant": "TRADER JOES #127", "category": "groceries"},
    ],
    "checking_6641": [
        {"id": "TXN-82001", "date": "2026-03-10", "amount": -1850.00,
         "merchant": "RENT PAYMENT", "category": "housing"},
        {"id": "TXN-82002", "date": "2026-03-09", "amount": -55.00,
         "merchant": "SPOTIFY + NETFLIX", "category": "subscriptions"},
    ],
    "checking_1198": [
        {"id": "TXN-83001", "date": "2026-03-10", "amount": -3200.00,
         "merchant": "MORTGAGE PAYMENT", "category": "housing"},
        {"id": "TXN-83002", "date": "2026-03-09", "amount": -450.00,
         "merchant": "WHOLE FOODS #555", "category": "groceries"},
    ],
    "checking_3301": [
        {"id": "TXN-84001", "date": "2026-03-10", "amount": -89.00,
         "merchant": "YOGA STUDIO", "category": "fitness"},
        {"id": "TXN-84002", "date": "2026-03-08", "amount": -220.00,
         "merchant": "ELECTRIC COMPANY", "category": "utilities"},
    ],
    "checking_2291": [
        {"id": "TXN-85001", "date": "2026-03-10", "amount": -145.00,
         "merchant": "T-MOBILE", "category": "utilities"},
    ],
    "checking_8834": [
        {"id": "TXN-86001", "date": "2026-03-10", "amount": -500.00,
         "merchant": "HEALTH INSURANCE", "category": "insurance"},
        {"id": "TXN-86002", "date": "2026-03-07", "amount": -38.90,
         "merchant": "WALGREENS #2201", "category": "pharmacy"},
    ],
}


class MockAccountService:
    async def get_balance(self, account_id: str) -> dict[str, Any]:
        data = _BALANCES.get(account_id, {"balance": 0.00, "currency": "USD"})
        return {
            "account": account_id,
            "balance": data["balance"],
            "currency": data["currency"],
            "as_of": datetime.now(timezone.utc).isoformat(),
        }

    async def get_transactions(self, account_or_card_id: str, **kwargs: Any) -> dict[str, Any]:
        txns = _TRANSACTIONS.get(account_or_card_id, [])

        # Filter by amount if provided
        amount_filter = kwargs.get("amount_filter")
        if amount_filter is not None:
            txns = [t for t in txns if abs(t["amount"]) == abs(amount_filter)]

        # Filter by date if provided
        date_filter = kwargs.get("date")
        if date_filter:
            txns = [t for t in txns if t["date"] == date_filter]

        return {"transactions": txns}
