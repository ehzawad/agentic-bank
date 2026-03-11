from __future__ import annotations

import logging
import time
from pathlib import Path

from fastapi import APIRouter, HTTPException

from chatbot.api.schemas import (
    ChatRequest,
    ChatResponse,
    CreateSessionResponse,
    HealthResponse,
    SessionStateResponse,
)
from chatbot.config import settings
from chatbot.engine.conversation import ConversationEngine
from chatbot.tools.handlers import ToolHandlerRegistry
from chatbot.tools.knowledge_base_tool import KnowledgeBaseToolHandler

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api")

# In-memory session store (for dev — production would use Redis/Postgres)
_sessions: dict[str, ConversationEngine] = {}
_session_timestamps: dict[str, float] = {}
_SESSION_TTL = 3600  # 1 hour
_MAX_SESSIONS = 1000

# Shared knowledge base — loaded once, reused across sessions
_kb_handler: KnowledgeBaseToolHandler | None = None


def _cleanup_sessions() -> None:
    """Remove expired sessions and enforce max session cap."""
    now = time.time()
    expired = [
        sid for sid, ts in _session_timestamps.items()
        if now - ts > _SESSION_TTL
    ]
    for sid in expired:
        _sessions.pop(sid, None)
        _session_timestamps.pop(sid, None)
    # Enforce max cap — evict oldest sessions first
    if len(_sessions) > _MAX_SESSIONS:
        sorted_sessions = sorted(_session_timestamps.items(), key=lambda x: x[1])
        to_remove = len(_sessions) - _MAX_SESSIONS
        for sid, _ in sorted_sessions[:to_remove]:
            _sessions.pop(sid, None)
            _session_timestamps.pop(sid, None)


def _get_knowledge_base() -> KnowledgeBaseToolHandler | None:
    """Lazy-init the knowledge base on first use."""
    global _kb_handler
    if _kb_handler is not None:
        return _kb_handler

    if not settings.openai_api_key:
        logger.warning("OPENAI_API_KEY not set — FAQ search will return low confidence for all queries")
        return None

    try:
        from chatbot.knowledge.vector_store import VectorStore
        from chatbot.knowledge.loader import load_faq_from_json

        faq_path = Path(__file__).parent.parent.parent / "data" / "knowledge_base" / "banking_faq.json"
        if not faq_path.exists():
            logger.warning(f"FAQ file not found at {faq_path}")
            return None

        store = VectorStore()
        if store.count == 0:
            count = load_faq_from_json(faq_path, store)
            logger.info(f"Loaded {count} FAQ entries into vector store")
        else:
            logger.info(f"Vector store already has {store.count} entries")

        _kb_handler = KnowledgeBaseToolHandler(store)
        return _kb_handler
    except Exception as e:
        logger.warning(f"Failed to initialize knowledge base: {e}")
        return None


@router.post("/sessions", response_model=CreateSessionResponse)
async def create_session() -> CreateSessionResponse:
    _cleanup_sessions()
    kb = _get_knowledge_base()
    engine = ConversationEngine()
    registry = ToolHandlerRegistry(knowledge_search=kb, session_store=engine.session_store)
    engine.tool_registry = registry
    _sessions[engine.session_id] = engine
    _session_timestamps[engine.session_id] = time.time()
    return CreateSessionResponse(
        session_id=engine.session_id,
        greeting=f"Welcome to {settings.bank_name}. How can I help you today?",
    )


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    _cleanup_sessions()
    engine = _sessions.get(request.session_id)
    if engine is None:
        raise HTTPException(status_code=404, detail="Session not found")

    _session_timestamps[request.session_id] = time.time()
    result = await engine.process_turn(request.message)

    return ChatResponse(
        response=result.response,
        state=result.state,
        emotion=result.emotion,
        tool_calls=result.tool_calls,
        transferred_to_human=result.transferred_to_human,
    )


@router.get("/sessions/{session_id}", response_model=SessionStateResponse)
async def get_session(session_id: str) -> SessionStateResponse:
    engine = _sessions.get(session_id)
    if engine is None:
        raise HTTPException(status_code=404, detail="Session not found")

    session = engine.session_store.session
    facts = engine.fact_store.get_current()
    threads = engine.thread_store.get_active() + engine.thread_store.get_suspended()
    readings = engine.emotion_store.state.readings

    return SessionStateResponse(
        session_id=session_id,
        state=engine.state_machine.state.value,
        verified=session.verified if session else False,
        customer_name=session.customer_name if session else None,
        facts=[f.model_dump() for f in facts],
        threads=[t.model_dump() for t in threads],
        emotion_trajectory=[r.label for r in readings],
    )


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str) -> dict:
    if session_id in _sessions:
        del _sessions[session_id]
    _session_timestamps.pop(session_id, None)
    return {"deleted": True}


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok", model=settings.model_name)
