"""ChromaDB vector store for FAQ/knowledge base.

Uses ChromaDB PersistentClient with OpenAI embedding function.
Per ChromaDB docs: get_or_create_collection for idempotent collection access.
"""

from __future__ import annotations

from typing import Any

import chromadb

from chatbot.config import settings
from chatbot.knowledge.embeddings import OpenAIEmbeddingFunction


class VectorStore:
    def __init__(
        self,
        collection_name: str = "banking_faq",
        persist_path: str | None = None,
        embedding_fn: OpenAIEmbeddingFunction | None = None,
    ) -> None:
        self._persist_path = persist_path or settings.chroma_path
        self._client = chromadb.PersistentClient(path=self._persist_path)
        self._ef = embedding_fn or OpenAIEmbeddingFunction()
        self._collection = self._client.get_or_create_collection(
            name=collection_name,
            embedding_function=self._ef,
            metadata={"hnsw:space": "cosine"},
        )

    def add_documents(
        self,
        documents: list[str],
        metadatas: list[dict[str, Any]] | None = None,
        ids: list[str] | None = None,
    ) -> None:
        if ids is None:
            ids = [f"doc_{i}" for i in range(len(documents))]
        self._collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids,
        )

    def query(self, query_text: str, n_results: int = 3) -> dict[str, Any]:
        """Query the collection. Returns ChromaDB query result dict."""
        # Use the embedding function's query method for proper input_type
        query_embedding = self._ef.embed_query(query_text)
        return self._collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            include=["documents", "metadatas", "distances"],
        )

    @property
    def count(self) -> int:
        return self._collection.count()
