"""All tool JSON schemas for the Anthropic API.

Claude sees these definitions and decides which tools to call.
"""

TOOLS: list[dict] = [
    # === ACCOUNT TOOLS ===
    {
        "name": "get_balance",
        "description": (
            "Get current balance for a specific account. "
            "Returns balance, currency, and timestamp."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "account_id": {
                    "type": "string",
                    "description": "Account identifier, e.g. 'checking_4821'",
                },
            },
            "required": ["account_id"],
        },
    },
    {
        "name": "get_transactions",
        "description": (
            "Get transactions for an account or card. "
            "Can filter by date and amount."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "account_or_card_id": {"type": "string"},
                "date": {
                    "type": "string",
                    "description": "Date in YYYY-MM-DD format",
                },
                "amount_filter": {
                    "type": "number",
                    "description": "Filter for a specific transaction amount",
                },
            },
            "required": ["account_or_card_id"],
        },
    },
    # === CARD TOOLS ===
    {
        "name": "block_card",
        "description": "Immediately block a card to prevent further transactions.",
        "input_schema": {
            "type": "object",
            "properties": {
                "card_id": {"type": "string"},
                "reason": {
                    "type": "string",
                    "enum": ["lost_wallet", "suspected_fraud", "customer_request"],
                },
            },
            "required": ["card_id", "reason"],
        },
    },
    {
        "name": "order_replacement_card",
        "description": "Order a replacement for a blocked card.",
        "input_schema": {
            "type": "object",
            "properties": {
                "card_id": {"type": "string"},
                "shipping": {
                    "type": "string",
                    "enum": ["standard", "expedited"],
                    "default": "expedited",
                },
            },
            "required": ["card_id"],
        },
    },
    {
        "name": "get_card_details",
        "description": "Get card details including APR, credit limit, current balance.",
        "input_schema": {
            "type": "object",
            "properties": {"card_id": {"type": "string"}},
            "required": ["card_id"],
        },
    },
    {
        "name": "block_merchant",
        "description": "Block a specific merchant from charging a card.",
        "input_schema": {
            "type": "object",
            "properties": {
                "card_id": {"type": "string"},
                "merchant_id": {"type": "string"},
            },
            "required": ["card_id", "merchant_id"],
        },
    },
    {
        "name": "file_dispute",
        "description": "File a dispute for unauthorized or incorrect transactions.",
        "input_schema": {
            "type": "object",
            "properties": {
                "card_id": {"type": "string"},
                "transaction_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "total_amount": {"type": "number"},
                "reason": {
                    "type": "string",
                    "enum": [
                        "unauthorized_recurring_charge",
                        "card_not_present_fraud",
                        "merchandise_not_received",
                        "incorrect_amount",
                        "other",
                    ],
                },
                "fraud_type": {"type": "string"},
                "card_possession": {"type": "string"},
                "last_authorized_transaction_id": {"type": "string"},
            },
            "required": ["card_id", "transaction_ids", "total_amount", "reason"],
        },
    },
    # === LOAN TOOLS ===
    {
        "name": "check_loan_eligibility",
        "description": (
            "Check if customer is eligible for a personal loan. "
            "Returns approved amount, offered rate, and term options."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "customer_id": {"type": "string"},
                "amount": {"type": "number"},
                "purpose": {
                    "type": "string",
                    "enum": [
                        "home_improvement", "debt_consolidation",
                        "major_purchase", "medical", "education", "other",
                    ],
                },
            },
            "required": ["customer_id", "amount", "purpose"],
        },
    },
    {
        "name": "calculate_emi",
        "description": "Calculate monthly EMI for a loan at a given rate and terms.",
        "input_schema": {
            "type": "object",
            "properties": {
                "amount": {"type": "number"},
                "rate": {
                    "type": "number",
                    "description": "Annual interest rate as percentage, e.g. 7.49",
                },
                "terms": {
                    "type": "array",
                    "items": {"type": "integer"},
                    "description": "Term lengths in months",
                },
            },
            "required": ["amount", "rate", "terms"],
        },
    },
    {
        "name": "check_mortgage_eligibility",
        "description": "Check mortgage pre-approval eligibility.",
        "input_schema": {
            "type": "object",
            "properties": {
                "customer_id": {"type": "string"},
                "home_price_range": {
                    "type": "array",
                    "items": {"type": "number"},
                    "description": "[min_price, max_price]",
                },
                "down_payment": {"type": "number"},
            },
            "required": ["customer_id", "home_price_range", "down_payment"],
        },
    },
    # === TRANSFER TOOLS ===
    {
        "name": "get_exchange_rate",
        "description": "Get current exchange rate between two currencies with fees.",
        "input_schema": {
            "type": "object",
            "properties": {
                "from_currency": {"type": "string"},
                "to_currency": {"type": "string"},
                "amount": {"type": "number"},
            },
            "required": ["from_currency", "to_currency", "amount"],
        },
    },
    {
        "name": "initiate_transfer",
        "description": "Initiate an international wire transfer.",
        "input_schema": {
            "type": "object",
            "properties": {
                "from_account": {"type": "string"},
                "recipient_name": {"type": "string"},
                "recipient_bank": {"type": "string"},
                "sort_code": {"type": "string"},
                "account_number": {"type": "string"},
                "recipient_address": {"type": "string"},
                "amount_usd": {"type": "number"},
                "target_currency": {"type": "string"},
                "purpose": {
                    "type": "string",
                    "enum": [
                        "family_support", "gift", "education",
                        "medical", "business", "other",
                    ],
                },
            },
            "required": [
                "from_account", "recipient_name", "recipient_bank",
                "account_number", "amount_usd", "target_currency", "purpose",
            ],
        },
    },
    # === DOCUMENT TOOLS ===
    {
        "name": "generate_statement",
        "description": "Generate an official bank statement PDF.",
        "input_schema": {
            "type": "object",
            "properties": {
                "account_id": {"type": "string"},
                "months": {"type": "integer"},
                "format": {"type": "string", "enum": ["pdf", "csv"], "default": "pdf"},
                "purpose": {"type": "string"},
            },
            "required": ["account_id", "months"],
        },
    },
    {
        "name": "get_tax_document",
        "description": "Retrieve tax document (e.g. 1099-INT) for a given tax year.",
        "input_schema": {
            "type": "object",
            "properties": {
                "customer_id": {"type": "string"},
                "tax_year": {"type": "integer"},
                "doc_type": {
                    "type": "string",
                    "enum": ["1099-INT", "1099-DIV", "1098"],
                    "default": "1099-INT",
                },
            },
            "required": ["customer_id", "tax_year"],
        },
    },
    {
        "name": "email_document",
        "description": "Email documents to the customer's email on file.",
        "input_schema": {
            "type": "object",
            "properties": {
                "document_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "email": {"type": "string"},
            },
            "required": ["document_ids"],
        },
    },
    # === COMPLAINT / ESCALATION TOOLS ===
    {
        "name": "get_complaint_history",
        "description": "Get open complaints and recent interaction history.",
        "input_schema": {
            "type": "object",
            "properties": {"customer_id": {"type": "string"}},
            "required": ["customer_id"],
        },
    },
    {
        "name": "get_case_status",
        "description": "Get current status of an open case or complaint.",
        "input_schema": {
            "type": "object",
            "properties": {"case_id": {"type": "string"}},
            "required": ["case_id"],
        },
    },
    {
        "name": "file_formal_complaint",
        "description": "File a formal complaint. Assigns priority and routes to department.",
        "input_schema": {
            "type": "object",
            "properties": {
                "customer_id": {"type": "string"},
                "related_case_id": {"type": "string"},
                "complaint_description": {"type": "string"},
                "priority": {
                    "type": "string",
                    "enum": ["normal", "high", "urgent"],
                },
            },
            "required": ["customer_id", "complaint_description", "priority"],
        },
    },
    {
        "name": "initiate_human_transfer",
        "description": (
            "Transfer the customer to a human agent. "
            "Include context so the customer doesn't repeat themselves."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "department": {
                    "type": "string",
                    "enum": [
                        "general", "fraud", "loans",
                        "senior_management", "client_relations",
                    ],
                },
                "priority": {
                    "type": "string",
                    "enum": ["normal", "high", "urgent"],
                },
                "context_summary": {"type": "string"},
                "customer_emotion": {"type": "string"},
            },
            "required": ["department", "priority", "context_summary"],
        },
    },
    # === KNOWLEDGE BASE ===
    {
        "name": "search_knowledge_base",
        "description": (
            "Search the bank's policy and FAQ knowledge base. "
            "Use for questions about policies, product features, eligibility, "
            "document requirements, processing times, fees, and general info. "
            "Returns answer text plus confidence level (high/medium/low)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": (
                        "Clear policy query. E.g. 'credit card eligibility requirements' "
                        "not 'am I eligible'"
                    ),
                },
            },
            "required": ["query"],
        },
    },
]
