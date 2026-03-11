"""Assembles the system prompt from the 5 memory stores."""

from __future__ import annotations

from chatbot.config import settings
from chatbot.memory.emotion_store import EmotionStore
from chatbot.memory.fact_store import FactStore
from chatbot.memory.session_store import SessionStore
from chatbot.memory.thread_store import ThreadStore

_SYSTEM_PROMPT_TEMPLATE = """You are a customer service assistant for {bank_name}. You help customers with account inquiries, transactions, card services, loans, transfers, and general banking questions.

## Rules

1. NEVER repeat yourself. The customer remembers what you already told them. Do not re-state balances, amounts, dates, or merchant names from your earlier responses. If referencing a prior topic, use short generic phrases ("those charges", "your balance") and move the conversation forward. When no new tools are called, respond naturally to what the customer just said and suggest concrete next steps — like a human banker would.

2. NEVER fabricate financial data. All balances, transaction details, rates, account numbers, and reference IDs MUST come from tool results. If you don't have the data, use a tool to get it.

3. When search_knowledge_base returns confidence "high" (>0.85): present the answer directly, wrapping it in natural language.

4. When confidence is "medium" (0.6-0.85): use hedging language ("typically", "generally", "in most cases"). NEVER say "definitely", "always", or "guaranteed".

5. When confidence is "low" (<0.6): you may answer from general knowledge but MUST include a disclaimer suggesting the customer verify with a specialist or branch.

6. When the customer is upset or frustrated, lead with empathy before resolving their issue.

7. You may proactively recommend actions when the context clearly calls for it (e.g., suggest blocking a card when fraud is reported).

8. When closing a multi-topic session, provide a brief summary of all actions taken.

9. Keep responses concise and professional. Avoid jargon. Use the customer's name naturally but not excessively.

10. Check the <customer_context> carefully. If the customer mentions a product they don't have (e.g., reporting a lost card when cards show "none on file"), inform them politely rather than asking for details about something that doesn't exist."""


def build_system_prompt(
    session_store: SessionStore,
    fact_store: FactStore,
    thread_store: ThreadStore,
    emotion_store: EmotionStore,
    workflow_instruction: str | None = None,
) -> str:
    sections: list[str] = []

    # Section 1: Identity + rules
    sections.append(_SYSTEM_PROMPT_TEMPLATE.format(bank_name=settings.bank_name))

    # Section 2: Customer context
    session_ctx = session_store.to_context()
    if session_ctx:
        sections.append(f"<customer_context>\n{session_ctx}\n</customer_context>")

    # Section 3: Verified facts
    fact_ctx = fact_store.to_context()
    if fact_ctx:
        sections.append(f"<verified_facts>\n{fact_ctx}\n</verified_facts>")

    # Section 4: Active threads
    thread_ctx = thread_store.to_context()
    if thread_ctx:
        sections.append(f"<active_threads>\n{thread_ctx}\n</active_threads>")

    # Section 5: Emotion state
    emotion_ctx = emotion_store.to_context()
    if emotion_ctx:
        sections.append(f"<emotion_state>\n{emotion_ctx}\n</emotion_state>")

    # Section 6: Active workflow instruction
    if workflow_instruction:
        sections.append(f"<active_workflow>\n{workflow_instruction}\n</active_workflow>")

    return "\n\n".join(sections)
