"""search_knowledge_base tool handler.

Wraps the vector store and returns answer + confidence tier.
"""

from __future__ import annotations

from chatbot.config import settings
from chatbot.knowledge.vector_store import VectorStore


class KnowledgeBaseToolHandler:
    def __init__(self, vector_store: VectorStore) -> None:
        self._store = vector_store

    async def search(self, query: str) -> dict:
        results = self._store.query(query, n_results=3)

        if not results or not results.get("distances") or not results["distances"][0]:
            return {
                "answer": None,
                "confidence": "low",
                "confidence_score": 0.0,
                "source": None,
            }

        # ChromaDB with cosine space returns distances (0 = identical, 2 = opposite)
        # Convert to similarity: similarity = 1 - (distance / 2)
        top_distance = results["distances"][0][0]
        top_score = 1 - (top_distance / 2)

        top_meta = results["metadatas"][0][0]
        answer = top_meta.get("answer", results["documents"][0][0])

        # Determine confidence tier
        if top_score >= settings.faq_high_threshold:
            confidence = "high"
        elif top_score >= settings.faq_medium_threshold:
            confidence = "medium"
        else:
            confidence = "low"

        return {
            "answer": answer,
            "confidence": confidence,
            "confidence_score": round(top_score, 3),
            "source": top_meta.get("source", "policy_document"),
            "category": top_meta.get("category", "general"),
        }
