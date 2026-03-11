"""OpenAI embedding function for ChromaDB.

Uses the OpenAI Python SDK per docs:
- client.embeddings.create(model="text-embedding-3-small", input=texts)
- Response: response.data[i].embedding
"""

from __future__ import annotations

from typing import Any, Dict

from openai import OpenAI
from chromadb import Documents, EmbeddingFunction, Embeddings
from chromadb.utils.embedding_functions import register_embedding_function

from chatbot.config import settings


@register_embedding_function
class OpenAIEmbeddingFunction(EmbeddingFunction[Documents]):
    """Custom ChromaDB embedding function wrapping OpenAI text-embedding-3-small.

    Registered with ChromaDB so collections auto-resolve on get_collection().
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
    ) -> None:
        self._client = OpenAI(api_key=api_key or settings.openai_api_key)
        self._model = model or settings.embedding_model

    def __call__(self, input: Documents) -> Embeddings:
        """Embed documents for storage."""
        if not input:
            return []
        # Batch in chunks of 2048 per OpenAI batch limit
        batch_size = 2048
        all_embeddings: list[list[float]] = []
        for i in range(0, len(input), batch_size):
            batch = input[i : i + batch_size]
            response = self._client.embeddings.create(
                model=self._model,
                input=batch,
            )
            all_embeddings.extend([d.embedding for d in response.data])
        return all_embeddings

    def embed_query(self, query: str) -> list[float]:
        """Embed a single query for search."""
        response = self._client.embeddings.create(
            model=self._model,
            input=query,
        )
        return response.data[0].embedding

    @staticmethod
    def name() -> str:
        return "openai-embedding"

    def get_config(self) -> Dict[str, Any]:
        return {"model": self._model}

    @staticmethod
    def build_from_config(config: Dict[str, Any]) -> "OpenAIEmbeddingFunction":
        return OpenAIEmbeddingFunction(model=config.get("model", "text-embedding-3-small"))
