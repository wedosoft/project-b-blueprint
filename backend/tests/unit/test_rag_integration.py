"""Unit tests for RAG (Retrieval-Augmented Generation) integration."""

from __future__ import annotations

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.repositories.conversation_repository import ConversationRepository
from app.schemas.conversation import MessagePayload, StartConversationRequest
from app.services.conversation_service import ConversationService
from app.services.llm_service import LLMResult, LLMService, LLMUsage
from app.services.qdrant_service import SearchResult


@pytest.fixture
def mock_llm_service():
    """Create a mocked LLM service."""
    service = AsyncMock(spec=LLMService)
    service.generate_completion = AsyncMock(
        return_value=LLMResult(
            provider="openai",
            model="gpt-4",
            content="참고 문서를 바탕으로 답변드립니다. 배송은 3-5일 소요됩니다.",
            latency_ms=200,
            usage=LLMUsage(
                prompt_tokens=150,
                completion_tokens=30,
                total_tokens=180,
            ),
        )
    )
    return service


@pytest.fixture
def mock_qdrant_service_with_results():
    """Create a mocked Qdrant service that returns search results."""
    service = AsyncMock()

    # Mock search results for similar documents
    search_results = [
        SearchResult(
            content="배송은 주문 후 3-5일 이내에 도착합니다",
            score=0.92,
            metadata={"doc_type": "faq", "category": "shipping"},
        ),
        SearchResult(
            content="배송 지연이 발생할 경우 고객센터로 연락 주세요",
            score=0.85,
            metadata={"doc_type": "policy", "category": "customer_service"},
        ),
    ]

    service.search_similar = AsyncMock(return_value=search_results)
    return service


@pytest.fixture
def conversation_repository():
    """Create a ConversationRepository instance."""
    return ConversationRepository()


@pytest.mark.asyncio
async def test_rag_integration_with_context_injection(
    conversation_repository,
    mock_llm_service,
    mock_qdrant_service_with_results,
):
    """Test that RAG pattern injects context into LLM prompt."""
    # Arrange
    customer_id = uuid4()
    org_id = uuid4()

    service = ConversationService(
        repository=conversation_repository,
        llm_service=mock_llm_service,
        qdrant_service=mock_qdrant_service_with_results,
    )

    payload = StartConversationRequest(
        customer_id=customer_id,
        organization_id=org_id,
        message=MessagePayload(
            body="배송이 언제 도착하나요?",
            attachments=[],
        ),
    )

    # Act
    response = await service.start_conversation(payload)

    # Assert: Qdrant search was called with correct parameters
    mock_qdrant_service_with_results.search_similar.assert_called_once()
    call_kwargs = mock_qdrant_service_with_results.search_similar.call_args.kwargs
    assert call_kwargs["query_text"] == "배송이 언제 도착하나요?"
    assert call_kwargs["limit"] == 3
    assert call_kwargs["score_threshold"] == 0.7
    assert call_kwargs["organization_id"] == str(org_id)

    # Assert: LLM was called with context-enriched prompt
    mock_llm_service.generate_completion.assert_called_once()
    llm_call_kwargs = mock_llm_service.generate_completion.call_args.kwargs
    messages = llm_call_kwargs["messages"]

    # System message should contain reference documents
    system_message = messages[0]["content"]
    assert "[참고 정보]" in system_message
    assert "참고 문서 1" in system_message
    assert "배송은 주문 후 3-5일" in system_message
    assert "참고 문서 2" in system_message
    assert "배송 지연" in system_message

    # User message should be the original query
    user_message = messages[1]["content"]
    assert user_message == "배송이 언제 도착하나요?"

    # Assert: Response includes AI message with context-aware answer
    assert len(response.messages) == 2
    ai_msg = response.messages[1]
    assert ai_msg.sender_type == "ai"
    assert "참고 문서" in ai_msg.body


@pytest.mark.asyncio
async def test_rag_graceful_degradation_when_search_fails(
    conversation_repository,
    mock_llm_service,
):
    """Test that conversation continues even when Qdrant search fails."""
    # Arrange: Qdrant service that raises exception
    failing_qdrant = AsyncMock()
    failing_qdrant.search_similar = AsyncMock(
        side_effect=Exception("Qdrant connection error")
    )

    service = ConversationService(
        repository=conversation_repository,
        llm_service=mock_llm_service,
        qdrant_service=failing_qdrant,
    )

    payload = StartConversationRequest(
        customer_id=uuid4(),
        message=MessagePayload(body="배송 문의", attachments=[]),
    )

    # Act
    response = await service.start_conversation(payload)

    # Assert: Conversation still succeeds without context
    assert len(response.messages) == 2
    assert response.messages[1].sender_type == "ai"

    # LLM should be called with basic prompt (no context)
    mock_llm_service.generate_completion.assert_called_once()
    llm_call_kwargs = mock_llm_service.generate_completion.call_args.kwargs
    system_message = llm_call_kwargs["messages"][0]["content"]
    assert "[참고 정보]" not in system_message  # No context injected


@pytest.mark.asyncio
async def test_rag_without_qdrant_service(
    conversation_repository,
    mock_llm_service,
):
    """Test that conversation works when Qdrant service is not provided."""
    # Arrange: No Qdrant service
    service = ConversationService(
        repository=conversation_repository,
        llm_service=mock_llm_service,
        qdrant_service=None,  # Explicitly None
    )

    payload = StartConversationRequest(
        customer_id=uuid4(),
        message=MessagePayload(body="안녕하세요", attachments=[]),
    )

    # Act
    response = await service.start_conversation(payload)

    # Assert: Works normally without RAG
    assert len(response.messages) == 2
    assert response.messages[1].sender_type == "ai"

    # LLM should be called with basic prompt
    mock_llm_service.generate_completion.assert_called_once()
    llm_call_kwargs = mock_llm_service.generate_completion.call_args.kwargs
    system_message = llm_call_kwargs["messages"][0]["content"]
    assert "[참고 정보]" not in system_message


@pytest.mark.asyncio
async def test_rag_with_no_search_results(
    conversation_repository,
    mock_llm_service,
):
    """Test RAG behavior when search returns no results."""
    # Arrange: Qdrant returns empty results (low similarity)
    empty_qdrant = AsyncMock()
    empty_qdrant.search_similar = AsyncMock(return_value=[])

    service = ConversationService(
        repository=conversation_repository,
        llm_service=mock_llm_service,
        qdrant_service=empty_qdrant,
    )

    payload = StartConversationRequest(
        customer_id=uuid4(),
        message=MessagePayload(body="completely unique query", attachments=[]),
    )

    # Act
    response = await service.start_conversation(payload)

    # Assert: Conversation succeeds without context
    assert len(response.messages) == 2

    # Qdrant was called but found nothing
    empty_qdrant.search_similar.assert_called_once()

    # LLM prompt should not contain context
    mock_llm_service.generate_completion.assert_called_once()
    llm_call_kwargs = mock_llm_service.generate_completion.call_args.kwargs
    system_message = llm_call_kwargs["messages"][0]["content"]
    assert "[참고 정보]" not in system_message


@pytest.mark.asyncio
async def test_rag_context_formatting(
    conversation_repository,
    mock_llm_service,
    mock_qdrant_service_with_results,
):
    """Test that context is properly formatted in system prompt."""
    service = ConversationService(
        repository=conversation_repository,
        llm_service=mock_llm_service,
        qdrant_service=mock_qdrant_service_with_results,
    )

    payload = StartConversationRequest(
        customer_id=uuid4(),
        message=MessagePayload(body="배송 문의", attachments=[]),
    )

    # Act
    await service.start_conversation(payload)

    # Assert: Check formatting of context in system prompt
    llm_call_kwargs = mock_llm_service.generate_completion.call_args.kwargs
    system_message = llm_call_kwargs["messages"][0]["content"]

    # Should contain section header
    assert "[참고 정보]" in system_message
    assert "과거 유사한 문의 사항들입니다" in system_message

    # Should contain numbered documents
    assert "참고 문서 1:" in system_message
    assert "참고 문서 2:" in system_message

    # Should contain actual content
    assert "배송은 주문 후 3-5일" in system_message
    assert "배송 지연이 발생할 경우" in system_message
