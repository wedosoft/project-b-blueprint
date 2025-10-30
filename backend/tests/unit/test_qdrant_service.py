"""Unit tests for QdrantService (mocked Qdrant and OpenAI)."""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

from app.services.qdrant_service import QdrantService, SearchResult
from core.config import (
    Settings,
    QdrantSettings,
    LLMSettings,
    SupabaseSettings,
    FlySettings,
    BackendSettings,
    FrontendSettings,
)
from pydantic import HttpUrl, SecretStr


@pytest.fixture
def mock_settings():
    """Create mock settings for testing."""
    return Settings(
        environment="development",
        supabase=SupabaseSettings(
            url=HttpUrl("https://test-supabase.example.com"),
            service_role_key=SecretStr("test-service-key"),
            anon_key=SecretStr("test-anon-key"),
        ),
        qdrant=QdrantSettings(
            url=HttpUrl("https://test-qdrant.example.com:6333"),
            api_key=SecretStr("test-qdrant-key"),
            collection="test-collection",
            vector_dimension=1536,
        ),
        llm=LLMSettings(
            provider="openai",
            openai_api_key=SecretStr("test-openai-key"),
        ),
        fly=FlySettings(
            app_name="test-app",
            api_token=SecretStr("test-fly-token"),
        ),
        backend=BackendSettings(
            base_url=HttpUrl("http://localhost:8000"),
        ),
        frontend=FrontendSettings(
            origin=HttpUrl("http://localhost:5173"),
        ),
    )


@pytest.fixture
def mock_openai_client():
    """Create mocked OpenAI client."""
    client = AsyncMock()

    # Mock embedding response
    mock_embedding_response = Mock()
    mock_embedding_response.data = [Mock(embedding=[0.1] * 1536)]
    client.embeddings.create = AsyncMock(return_value=mock_embedding_response)

    return client


@pytest.fixture
def mock_qdrant_async_client():
    """Create mocked async Qdrant client."""
    client = AsyncMock()
    return client


@pytest.fixture
def mock_qdrant_sync_client():
    """Create mocked sync Qdrant client."""
    client = Mock()
    return client


@pytest.fixture
def qdrant_service(mock_settings, mock_openai_client):
    """Create QdrantService with mocked dependencies."""
    with patch("app.services.qdrant_service.AsyncQdrantClient") as mock_async_class, \
         patch("app.services.qdrant_service.QdrantClient") as mock_sync_class:

        service = QdrantService(
            settings=mock_settings,
            openai_client=mock_openai_client,
        )

        # Replace clients with mocks
        service._async_client = AsyncMock()
        service._sync_client = Mock()

        yield service


@pytest.mark.asyncio
async def test_generate_embedding_success(qdrant_service, mock_openai_client):
    """Test successful embedding generation."""
    text = "안녕하세요, 배송 문의 드립니다"

    embedding = await qdrant_service.generate_embedding(text)

    assert len(embedding) == 1536
    assert all(isinstance(val, float) for val in embedding)

    # Verify OpenAI API was called correctly
    mock_openai_client.embeddings.create.assert_called_once()
    call_kwargs = mock_openai_client.embeddings.create.call_args.kwargs
    assert call_kwargs["model"] == "text-embedding-3-small"
    assert call_kwargs["input"] == text


@pytest.mark.asyncio
async def test_generate_embedding_failure(qdrant_service, mock_openai_client):
    """Test embedding generation with API failure."""
    mock_openai_client.embeddings.create = AsyncMock(
        side_effect=Exception("OpenAI API error")
    )

    with pytest.raises(Exception, match="OpenAI API error"):
        await qdrant_service.generate_embedding("test text")


@pytest.mark.asyncio
async def test_search_similar_with_results(qdrant_service):
    """Test vector search with matching results."""
    # Mock search results
    mock_hit1 = Mock()
    mock_hit1.score = 0.95
    mock_hit1.payload = {
        "content": "배송 문의에 대한 답변입니다",
        "doc_type": "ticket",
        "status": "closed",
    }

    mock_hit2 = Mock()
    mock_hit2.score = 0.88
    mock_hit2.payload = {
        "content": "배송 지연 안내",
        "doc_type": "faq",
    }

    qdrant_service._async_client.search = AsyncMock(
        return_value=[mock_hit1, mock_hit2]
    )

    results = await qdrant_service.search_similar(
        query_text="배송이 언제 도착하나요?",
        limit=5,
        score_threshold=0.7,
    )

    assert len(results) == 2
    assert isinstance(results[0], SearchResult)
    assert results[0].score == 0.95
    assert "배송 문의" in results[0].content
    assert results[0].metadata["doc_type"] == "ticket"

    assert results[1].score == 0.88
    assert "배송 지연" in results[1].content


@pytest.mark.asyncio
async def test_search_similar_with_organization_filter(qdrant_service):
    """Test vector search with organization ID filter."""
    org_id = str(uuid4())
    qdrant_service._async_client.search = AsyncMock(return_value=[])

    await qdrant_service.search_similar(
        query_text="test query",
        organization_id=org_id,
    )

    # Verify filter was applied
    call_kwargs = qdrant_service._async_client.search.call_args.kwargs
    assert call_kwargs["query_filter"] is not None


@pytest.mark.asyncio
async def test_search_similar_returns_empty_on_error(qdrant_service):
    """Test graceful degradation when search fails."""
    qdrant_service._async_client.search = AsyncMock(
        side_effect=Exception("Qdrant connection error")
    )

    results = await qdrant_service.search_similar("test query")

    # Should return empty list instead of raising
    assert results == []


@pytest.mark.asyncio
async def test_upsert_document_success(qdrant_service):
    """Test successful document upsert."""
    doc_id = str(uuid4())
    content = "이것은 테스트 문서입니다"
    metadata = {
        "organization_id": str(uuid4()),
        "doc_type": "faq",
        "tags": ["배송", "문의"],
    }

    qdrant_service._async_client.upsert = AsyncMock()

    success = await qdrant_service.upsert_document(
        document_id=doc_id,
        content=content,
        metadata=metadata,
    )

    assert success is True

    # Verify upsert was called
    qdrant_service._async_client.upsert.assert_called_once()
    call_kwargs = qdrant_service._async_client.upsert.call_args.kwargs
    assert call_kwargs["collection_name"] == "test-collection"

    points = call_kwargs["points"]
    assert len(points) == 1
    assert points[0].id == doc_id
    assert len(points[0].vector) == 1536
    assert points[0].payload["content"] == content
    assert "updated_at" in points[0].payload


@pytest.mark.asyncio
async def test_upsert_document_failure(qdrant_service):
    """Test document upsert with failure."""
    qdrant_service._async_client.upsert = AsyncMock(
        side_effect=Exception("Qdrant error")
    )

    success = await qdrant_service.upsert_document(
        document_id="test-id",
        content="test content",
        metadata={},
    )

    assert success is False


def test_ensure_collection_exists_already_exists(qdrant_service):
    """Test collection existence check when collection exists."""
    qdrant_service._sync_client.collection_exists = Mock(return_value=True)

    result = qdrant_service.ensure_collection_exists()

    assert result is True
    qdrant_service._sync_client.collection_exists.assert_called_once_with("test-collection")
    qdrant_service._sync_client.create_collection.assert_not_called()


def test_ensure_collection_creates_when_missing(qdrant_service):
    """Test collection creation when it doesn't exist."""
    qdrant_service._sync_client.collection_exists = Mock(return_value=False)
    qdrant_service._sync_client.create_collection = Mock()

    result = qdrant_service.ensure_collection_exists()

    assert result is True
    qdrant_service._sync_client.create_collection.assert_called_once()

    call_kwargs = qdrant_service._sync_client.create_collection.call_args.kwargs
    assert call_kwargs["collection_name"] == "test-collection"
    assert call_kwargs["vectors_config"].size == 1536


def test_ensure_collection_handles_error(qdrant_service):
    """Test error handling in collection creation."""
    qdrant_service._sync_client.collection_exists = Mock(
        side_effect=Exception("Connection error")
    )

    result = qdrant_service.ensure_collection_exists()

    assert result is False


@pytest.mark.asyncio
async def test_close(qdrant_service):
    """Test closing Qdrant clients."""
    qdrant_service._async_client.close = AsyncMock()
    qdrant_service._sync_client.close = Mock()

    await qdrant_service.close()

    qdrant_service._async_client.close.assert_called_once()
    qdrant_service._sync_client.close.assert_called_once()
