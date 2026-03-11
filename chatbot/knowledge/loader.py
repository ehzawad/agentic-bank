"""Loads FAQ/policy documents into the vector store."""

from __future__ import annotations

import json
from pathlib import Path

from chatbot.knowledge.vector_store import VectorStore


def load_faq_from_json(file_path: str | Path, vector_store: VectorStore) -> int:
    """Load FAQ entries from a JSON file into the vector store.

    Expected format: list of {"id": str, "question": str, "answer": str, "category": str}
    """
    path = Path(file_path)
    with path.open() as f:
        entries = json.load(f)

    documents: list[str] = []
    metadatas: list[dict] = []
    ids: list[str] = []

    for entry in entries:
        # Combine question and answer as the document for embedding
        doc_text = f"Q: {entry['question']}\nA: {entry['answer']}"
        documents.append(doc_text)
        metadatas.append({
            "category": entry.get("category", "general"),
            "source": "banking_faq",
            "answer": entry["answer"],
            "question": entry["question"],
        })
        ids.append(entry.get("id", f"faq_{len(ids)}"))

    vector_store.add_documents(documents=documents, metadatas=metadatas, ids=ids)
    return len(documents)
