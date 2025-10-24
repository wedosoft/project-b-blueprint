"""Vector search service for knowledge base using Qdrant."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import List
from uuid import UUID

from openai import AsyncOpenAI
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, FieldCondition, Filter, MatchValue, VectorParams

from backend.core.config import get_settings

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class KnowledgeSearchResult:
    """A single knowledge base search result."""

    knowledge_item_id: UUID
    title: str
    content: str
    score: float
    source_uri: str | None = None


class VectorSearchService:
    """Search knowledge base using vector similarity."""

    def __init__(self) -> None:
        self._settings = get_settings()

        # Initialize Qdrant client
        self._qdrant_client = QdrantClient(
            url=str(self._settings.qdrant.url),
            api_key=self._settings.qdrant.api_key.get_secret_value(),
        )

        # Initialize OpenAI for embeddings
        self._openai_client: AsyncOpenAI | None = None
        if self._settings.llm.openai_api_key:
            self._openai_client = AsyncOpenAI(
                api_key=self._settings.llm.openai_api_key.get_secret_value(),
            )

    async def search_knowledge_base(
        self,
        query: str,
        organization_id: UUID,
        limit: int = 3,
        score_threshold: float = 0.7,
    ) -> List[KnowledgeSearchResult]:
        """Search knowledge base for relevant content.

        Args:
            query: User's question or query text
            organization_id: Filter results by organization
            limit: Maximum number of results to return
            score_threshold: Minimum similarity score (0.0 to 1.0)

        Returns:
            List of relevant knowledge items with similarity scores
        """
        if not self._openai_client:
            logger.warning("OpenAI client not configured, cannot perform vector search")
            return []

        try:
            # Generate embedding for query
            embedding_response = await self._openai_client.embeddings.create(
                model="text-embedding-3-small",
                input=query,
            )
            query_vector = embedding_response.data[0].embedding

            # Search in Qdrant
            search_results = self._qdrant_client.search(
                collection_name=self._settings.qdrant.collection,
                query_vector=query_vector,
                query_filter=Filter(
                    must=[
                        FieldCondition(
                            key="organization_id",
                            match=MatchValue(value=str(organization_id)),
                        ),
                        FieldCondition(
                            key="is_active",
                            match=MatchValue(value=True),
                        ),
                    ]
                ),
                limit=limit,
                score_threshold=score_threshold,
            )

            # Convert to KnowledgeSearchResult
            results = []
            for hit in search_results:
                payload = hit.payload or {}
                results.append(
                    KnowledgeSearchResult(
                        knowledge_item_id=UUID(payload.get("knowledge_item_id", payload.get("id"))),
                        title=payload.get("title", ""),
                        content=payload.get("content", ""),
                        score=hit.score,
                        source_uri=payload.get("source_uri"),
                    )
                )

            logger.info(
                "Vector search returned %d results for organization %s",
                len(results),
                organization_id,
            )
            return results

        except Exception as exc:
            logger.error("Vector search failed: %s", exc, exc_info=True)
            return []

    def ensure_collection_exists(self) -> None:
        """Create Qdrant collection if it doesn't exist."""
        try:
            collections = self._qdrant_client.get_collections()
            collection_names = [col.name for col in collections.collections]

            if self._settings.qdrant.collection not in collection_names:
                logger.info(
                    "Creating Qdrant collection: %s",
                    self._settings.qdrant.collection,
                )
                self._qdrant_client.create_collection(
                    collection_name=self._settings.qdrant.collection,
                    vectors_config=VectorParams(
                        size=self._settings.qdrant.vector_dimension,
                        distance=Distance.COSINE,
                    ),
                )
                logger.info("Collection created successfully")
        except Exception as exc:
            logger.error("Failed to ensure collection exists: %s", exc)
            raise


__all__ = ["VectorSearchService", "KnowledgeSearchResult"]
