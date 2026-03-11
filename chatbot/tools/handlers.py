"""Maps Claude tool names to service adapter calls."""

from __future__ import annotations

import json
from typing import Any

from chatbot.services.mock.accounts import MockAccountService
from chatbot.services.mock.cards import MockCardService
from chatbot.services.mock.complaints import MockComplaintService
from chatbot.services.mock.documents import MockDocumentService
from chatbot.services.mock.loans import MockLoanService
from chatbot.services.mock.transfers import MockTransferService
from chatbot.memory.session_store import SessionStore


class ToolHandlerRegistry:
    def __init__(
        self,
        accounts: MockAccountService | None = None,
        cards: MockCardService | None = None,
        loans: MockLoanService | None = None,
        transfers: MockTransferService | None = None,
        documents: MockDocumentService | None = None,
        complaints: MockComplaintService | None = None,
        knowledge_search: Any = None,
        session_store: SessionStore | None = None,
    ) -> None:
        self.accounts = accounts or MockAccountService()
        self.cards = cards or MockCardService()
        self.loans = loans or MockLoanService()
        self.transfers = transfers or MockTransferService()
        self.documents = documents or MockDocumentService()
        self.complaints = complaints or MockComplaintService()
        self.knowledge_search = knowledge_search
        self.session_store = session_store

        self._handlers: dict[str, Any] = {
            "get_balance": self._get_balance,
            "get_transactions": self._get_transactions,
            "block_card": self._block_card,
            "order_replacement_card": self._order_replacement_card,
            "get_card_details": self._get_card_details,
            "block_merchant": self._block_merchant,
            "file_dispute": self._file_dispute,
            "check_loan_eligibility": self._check_loan_eligibility,
            "calculate_emi": self._calculate_emi,
            "check_mortgage_eligibility": self._check_mortgage_eligibility,
            "get_exchange_rate": self._get_exchange_rate,
            "initiate_transfer": self._initiate_transfer,
            "generate_statement": self._generate_statement,
            "get_tax_document": self._get_tax_document,
            "email_document": self._email_document,
            "get_complaint_history": self._get_complaint_history,
            "get_case_status": self._get_case_status,
            "file_formal_complaint": self._file_formal_complaint,
            "initiate_human_transfer": self._initiate_human_transfer,
            "search_knowledge_base": self._search_knowledge_base,
        }

    def has_tool(self, name: str) -> bool:
        return name in self._handlers

    async def execute(self, tool_name: str, tool_input: dict[str, Any]) -> str:
        handler = self._handlers.get(tool_name)
        if handler is None:
            return json.dumps({"error": f"Unknown tool: {tool_name}"})
        result = await handler(tool_input)
        return json.dumps(result, default=str)

    _ACCESS_DENIED = {"error": "Access denied: resource does not belong to authenticated customer"}

    def _check_access(self, resource_id: str, resource_type: str) -> str | None:
        """Return an error string if access is denied, or None if allowed."""
        if self.session_store is None:
            return None
        session = self.session_store.session
        if session is None or not session.verified:
            return "Access denied: customer not verified"
        if resource_type == "account":
            if resource_id not in session.accounts:
                return "Access denied: resource does not belong to authenticated customer"
        elif resource_type == "card":
            if resource_id not in session.cards:
                return "Access denied: resource does not belong to authenticated customer"
        elif resource_type == "customer":
            if resource_id != session.customer_id:
                return "Access denied: resource does not belong to authenticated customer"
        return None

    # --- Account ---
    async def _get_balance(self, inp: dict) -> dict:
        err = self._check_access(inp["account_id"], "account")
        if err:
            return self._ACCESS_DENIED
        return await self.accounts.get_balance(inp["account_id"])

    async def _get_transactions(self, inp: dict) -> dict:
        resource_id = inp["account_or_card_id"]
        err_account = self._check_access(resource_id, "account")
        err_card = self._check_access(resource_id, "card")
        if err_account and err_card:
            return self._ACCESS_DENIED
        return await self.accounts.get_transactions(
            inp["account_or_card_id"],
            date=inp.get("date"),
            amount_filter=inp.get("amount_filter"),
        )

    # --- Cards ---
    async def _block_card(self, inp: dict) -> dict:
        err = self._check_access(inp["card_id"], "card")
        if err:
            return self._ACCESS_DENIED
        return await self.cards.block_card(inp["card_id"], inp["reason"])

    async def _order_replacement_card(self, inp: dict) -> dict:
        err = self._check_access(inp["card_id"], "card")
        if err:
            return self._ACCESS_DENIED
        return await self.cards.order_replacement(inp["card_id"], inp.get("shipping", "expedited"))

    async def _get_card_details(self, inp: dict) -> dict:
        err = self._check_access(inp["card_id"], "card")
        if err:
            return self._ACCESS_DENIED
        return await self.cards.get_details(inp["card_id"])

    async def _block_merchant(self, inp: dict) -> dict:
        err = self._check_access(inp["card_id"], "card")
        if err:
            return self._ACCESS_DENIED
        return await self.cards.block_merchant(inp["card_id"], inp["merchant_id"])

    async def _file_dispute(self, inp: dict) -> dict:
        err = self._check_access(inp["card_id"], "card")
        if err:
            return self._ACCESS_DENIED
        return await self.cards.file_dispute(**inp)

    # --- Loans ---
    async def _check_loan_eligibility(self, inp: dict) -> dict:
        err = self._check_access(inp["customer_id"], "customer")
        if err:
            return self._ACCESS_DENIED
        return await self.loans.check_eligibility(inp["customer_id"], inp["amount"], inp["purpose"])

    async def _calculate_emi(self, inp: dict) -> dict:
        return await self.loans.calculate_emi(inp["amount"], inp["rate"], inp["terms"])

    async def _check_mortgage_eligibility(self, inp: dict) -> dict:
        return await self.loans.check_mortgage_eligibility(**inp)

    # --- Transfers ---
    async def _get_exchange_rate(self, inp: dict) -> dict:
        return await self.transfers.get_exchange_rate(
            inp["from_currency"], inp["to_currency"], inp["amount"]
        )

    async def _initiate_transfer(self, inp: dict) -> dict:
        return await self.transfers.initiate_transfer(**inp)

    # --- Documents ---
    async def _generate_statement(self, inp: dict) -> dict:
        return await self.documents.generate_statement(
            inp["account_id"], inp["months"], **{k: v for k, v in inp.items() if k not in ("account_id", "months")}
        )

    async def _get_tax_document(self, inp: dict) -> dict:
        err = self._check_access(inp["customer_id"], "customer")
        if err:
            return self._ACCESS_DENIED
        return await self.documents.get_tax_document(
            inp["customer_id"], inp["tax_year"], inp.get("doc_type", "1099-INT")
        )

    async def _email_document(self, inp: dict) -> dict:
        return await self.documents.email_document(inp["document_ids"], inp.get("email"))

    # --- Complaints ---
    async def _get_complaint_history(self, inp: dict) -> dict:
        err = self._check_access(inp["customer_id"], "customer")
        if err:
            return self._ACCESS_DENIED
        return await self.complaints.get_history(inp["customer_id"])

    async def _get_case_status(self, inp: dict) -> dict:
        return await self.complaints.get_case_status(inp["case_id"])

    async def _file_formal_complaint(self, inp: dict) -> dict:
        return await self.complaints.file_complaint(**inp)

    async def _initiate_human_transfer(self, inp: dict) -> dict:
        return await self.complaints.initiate_human_transfer(**inp)

    # --- Knowledge Base ---
    async def _search_knowledge_base(self, inp: dict) -> dict:
        if self.knowledge_search is None:
            return {"answer": None, "confidence": "low", "confidence_score": 0.0}
        return await self.knowledge_search.search(inp["query"])
