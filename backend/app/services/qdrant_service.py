"""Qdrant vector search service for RAG pattern."""

from __future__ import annotations

import logging
from typing import List, Dict, Any
from datetime import datetime, timezone
from uuid import uuid5, NAMESPACE_DNS

from qdrant_client import QdrantClient, AsyncQdrantClient
from qdrant_client.http import models as rest_models
from openai import AsyncOpenAI

from core.config import Settings

logger = logging.getLogger(__name__)


class SearchResult:
    """Vector search result with similarity score."""

    def __init__(
        self,
        content: str,
        score: float,
        metadata: Dict[str, Any],
    ):
        self.content = content
        self.score = score
        self.metadata = metadata


class QdrantService:
    """Service for vector search using Qdrant and OpenAI embeddings."""

    def __init__(self, settings: Settings, openai_client: AsyncOpenAI):
        """Initialize Qdrant service with settings and OpenAI client.

        Args:
            settings: Application settings containing Qdrant configuration
            openai_client: AsyncOpenAI client for embedding generation
        """
        self._settings = settings
        self._openai_client = openai_client
        self._collection = settings.qdrant.collection
        self._dimension = settings.qdrant.vector_dimension

        # Async client for production use
        self._async_client = AsyncQdrantClient(
            url=str(settings.qdrant.url),
            api_key=settings.qdrant.api_key.get_secret_value(),
            timeout=30,
        )

        # Sync client for initialization/testing
        self._sync_client = QdrantClient(
            url=str(settings.qdrant.url),
            api_key=settings.qdrant.api_key.get_secret_value(),
            timeout=30,
        )

    async def generate_embedding(self, text: str) -> List[float]:
        """Generate vector embedding for text using OpenAI.

        Args:
            text: Input text to embed

        Returns:
            Vector embedding as list of floats
        """
        try:
            response = await self._openai_client.embeddings.create(
                model="text-embedding-3-large",  # 3072 dimensions to match collection
                input=text,
                encoding_format="float",
            )
            return response.data[0].embedding
        except Exception as exc:
            logger.error(f"Failed to generate embedding: {exc}")
            raise

    async def search_similar(
        self,
        query_text: str,
        limit: int = 5,
        score_threshold: float = 0.7,
        organization_id: str | None = None,
    ) -> List[SearchResult]:
        """Search for similar documents using vector similarity.

        Args:
            query_text: User query to search for
            limit: Maximum number of results to return
            score_threshold: Minimum similarity score (0-1)
            organization_id: Optional filter by organization

        Returns:
            List of SearchResult objects sorted by similarity
        """
        # Generate query embedding
        query_vector = await self.generate_embedding(query_text)

        # Build filter conditions
        filter_conditions: List[rest_models.Condition] = []
        if organization_id:
            filter_conditions.append(
                rest_models.FieldCondition(
                    key="organization_id",
                    match=rest_models.MatchValue(value=organization_id),
                )
            )

        search_filter = (
            rest_models.Filter(must=filter_conditions) if filter_conditions else None
        )

        # Search using async client (with named vector support)
        try:
            search_results = await self._async_client.search(
                collection_name=self._collection,
                query_vector=("dense", query_vector),  # Named vector for 'documents' collection
                limit=limit,
                score_threshold=score_threshold,
                query_filter=search_filter,
                with_payload=True,
            )

            # Convert to SearchResult objects
            results: List[SearchResult] = []
            for hit in search_results:
                content = hit.payload.get("content", "")
                metadata = {
                    k: v for k, v in hit.payload.items() if k != "content"
                }
                results.append(
                    SearchResult(
                        content=content,
                        score=hit.score,
                        metadata=metadata,
                    )
                )

            logger.info(
                f"Vector search found {len(results)} results for query: {query_text[:50]}..."
            )
            return results

        except Exception as exc:
            logger.error(f"Vector search failed: {exc}")
            # Return empty results on error (graceful degradation)
            return []

    async def upsert_document(
        self,
        document_id: str,
        content: str,
        metadata: Dict[str, Any],
    ) -> bool:
        """Store or update a document in the vector database.

        Args:
            document_id: Unique identifier for the document
            content: Document text content
            metadata: Additional metadata (organization_id, tags, etc.)

        Returns:
            True if successful, False otherwise
        """
        try:
            # Generate embedding
            vector = await self.generate_embedding(content)

            # Convert string ID to UUID (Qdrant requirement)
            # Use UUID5 to generate deterministic UUID from document_id
            point_id = str(uuid5(NAMESPACE_DNS, document_id))

            # Prepare payload
            payload = {
                "document_id": document_id,  # Store original ID in payload
                "content": content,
                "updated_at": datetime.now(timezone.utc).isoformat(),
                **metadata,
            }

            # Upsert to Qdrant (with named vector support)
            await self._async_client.upsert(
                collection_name=self._collection,
                points=[
                    rest_models.PointStruct(
                        id=point_id,
                        vector={"dense": vector},  # Named vector for 'documents' collection
                        payload=payload,
                    )
                ],
            )

            logger.info(f"Document upserted successfully: {document_id}")
            return True

        except Exception as exc:
            logger.error(f"Failed to upsert document {document_id}: {exc}")
            return False

    def ensure_collection_exists(self) -> bool:
        """Ensure the Qdrant collection exists with correct configuration.

        Returns:
            True if collection exists or was created, False on error
        """
        try:
            # Check if collection exists
            if self._sync_client.collection_exists(self._collection):
                logger.info(f"Qdrant collection '{self._collection}' already exists")
                return True

            # Create collection
            self._sync_client.create_collection(
                collection_name=self._collection,
                vectors_config=rest_models.VectorParams(
                    size=self._dimension,
                    distance=rest_models.Distance.COSINE,
                ),
                optimizers_config=rest_models.OptimizersConfigDiff(
                    indexing_threshold=20_000
                ),
                on_disk_payload=True,
            )

            logger.info(f"Qdrant collection '{self._collection}' created successfully")
            return True

        except Exception as exc:
            logger.error(f"Failed to ensure collection exists: {exc}")
            return False

    async def close(self) -> None:
        """Close Qdrant client connections."""
        try:
            await self._async_client.close()
            self._sync_client.close()
        except Exception as exc:
            logger.error(f"Error closing Qdrant clients: {exc}")


__all__ = ["QdrantService", "SearchResult"]
