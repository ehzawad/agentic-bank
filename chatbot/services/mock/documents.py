from __future__ import annotations

import uuid
from typing import Any


class MockDocumentService:
    async def generate_statement(
        self, account_id: str, months: int, **kwargs: Any
    ) -> dict[str, Any]:
        stmt_id = f"STM-{account_id.split('_')[-1]}-{months}M"
        return {
            "statement_id": stmt_id,
            "period": f"Sep 2025 - Mar 2026" if months == 6 else f"Last {months} months",
            "pages": max(4, months * 2),
            "download_url": f"/statements/{stmt_id}.pdf",
            "stamped": True,
            "format": kwargs.get("format", "pdf"),
        }

    async def get_tax_document(
        self, customer_id: str, tax_year: int, doc_type: str = "1099-INT"
    ) -> dict[str, Any]:
        return {
            "document_id": f"TAX-{doc_type}-{tax_year}-{customer_id.split('_')[-1]}",
            "tax_year": tax_year,
            "doc_type": doc_type,
            "interest_earned": 847.32,
            "available": True,
            "download_url": f"/tax/TAX-{doc_type}-{tax_year}.pdf",
        }

    async def email_document(
        self, document_ids: list[str], email: str | None = None
    ) -> dict[str, Any]:
        return {
            "sent": True,
            "to": email or "customer@email.com",
            "documents": document_ids,
        }
