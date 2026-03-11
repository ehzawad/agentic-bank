from __future__ import annotations

import uuid
from typing import Any


_COMPLAINT_HISTORY: dict[str, dict[str, Any]] = {
    "thomas_wright_1198": {
        "open_cases": [
            {
                "case_id": "CMP-2026-3341",
                "subject": "Wire transfer to wrong account",
                "opened": "2026-02-25",
                "status": "pending_review",
                "last_agent": "Agent_44",
                "notes": (
                    "Customer reported $5,000 wire sent to wrong account. "
                    "Recall initiated but not confirmed. Customer called back 2x, "
                    "no resolution communicated."
                ),
            }
        ],
        "interaction_count_30d": 5,
    },
}

_CASE_STATUS: dict[str, dict[str, Any]] = {
    "CMP-2026-3341": {
        "case_id": "CMP-2026-3341",
        "status": "recall_confirmed",
        "recall_status": "funds_recovered",
        "recovered_amount": 5000.00,
        "credit_to_account": "pending_manual_approval",
        "blocker": "requires_manager_sign_off",
        "last_updated": "2026-03-09",
    },
}


class MockComplaintService:
    async def get_history(self, customer_id: str) -> dict[str, Any]:
        return _COMPLAINT_HISTORY.get(customer_id, {"open_cases": [], "interaction_count_30d": 0})

    async def get_case_status(self, case_id: str) -> dict[str, Any]:
        return _CASE_STATUS.get(case_id, {"case_id": case_id, "status": "not_found"})

    async def file_complaint(self, **kwargs: Any) -> dict[str, Any]:
        return {
            "complaint_id": f"FML-2026-{uuid.uuid4().int % 10000:04d}",
            "priority": kwargs.get("priority", "normal"),
            "assigned_to": "Senior Manager - Client Relations",
            "status": "open",
        }

    async def initiate_human_transfer(self, **kwargs: Any) -> dict[str, Any]:
        return {
            "transfer_id": f"HT-{uuid.uuid4().hex[:8]}",
            "department": kwargs.get("department", "general"),
            "priority": kwargs.get("priority", "normal"),
            "status": "connecting",
            "estimated_wait": "< 1 minute",
        }
