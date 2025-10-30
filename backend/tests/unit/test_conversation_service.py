"""Unit tests for ConversationService with LLM integration."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest

from app.repositories.conversation_repository import (
    ConversationRecord,
    ConversationRepository,
    MessageRecord,
)
from app.schemas.conversation import MessagePayload, StartConversationRequest
from app.services.conversation_service import ConversationService
from app.services.llm_service import LLMResult, LLMService, LLMUsage


@pytest.fixture
def mock_llm_service():
    """Create a mocked LLM service."""
    service = AsyncMock(spec=LLMService)
    service.generate_completion = AsyncMock(
        return_value=LLMResult(
            provider="openai",
            model="gpt-4",
            content="안녕하세요! 무엇을 도와드릴까요?",
            latency_ms=150,
            usage=LLMUsage(
                prompt_tokens=50,
                completion_tokens=20,
                total_tokens=70,
            ),
        )
    )
    return service


@pytest.fixture
def conversation_repository():
    """Create a ConversationRepository instance."""
    return ConversationRepository()


@pytest.fixture
def mock_qdrant_service():
    """Create a mocked Qdrant service (optional dependency)."""
    service = AsyncMock()
    # Mock search_similar to return empty results by default
    service.search_similar = AsyncMock(return_value=[])
    return service


@pytest.fixture
def conversation_service(conversation_repository, mock_llm_service, mock_qdrant_service):
    """Create a ConversationService with mocked dependencies."""
    return ConversationService(
        repository=conversation_repository,
        llm_service=mock_llm_service,
        qdrant_service=mock_qdrant_service,
    )


@pytest.mark.asyncio
async def test_start_conversation_creates_conversation_and_ai_response(
    conversation_service: ConversationService,
    mock_llm_service: AsyncMock,
):
    """Test that starting a conversation creates both customer message and AI response."""
    # Arrange
    customer_id = uuid4()
    payload = StartConversationRequest(
        customer_id=customer_id,
        message=MessagePayload(
            body="상품 문의 드립니다",
            attachments=[],
        ),
        metadata={"source": "web"},
    )

    # Act
    response = await conversation_service.start_conversation(payload)

    # Assert
    assert response.conversation.customer_id == customer_id
    assert response.conversation.status == "active"
    assert response.conversation.channel == "text-web"
    assert response.conversation.metadata == {"source": "web"}
    assert len(response.messages) == 2

    # 첫 번째 메시지: 고객 메시지
    customer_msg = response.messages[0]
    assert customer_msg.sender_type == "customer"
    assert customer_msg.body == "상품 문의 드립니다"
    assert customer_msg.sequence == 1

    # 두 번째 메시지: AI 응답
    ai_msg = response.messages[1]
    assert ai_msg.sender_type == "ai"
    assert ai_msg.body == "안녕하세요! 무엇을 도와드릴까요?"
    assert ai_msg.sequence == 2

    # LLM 서비스가 올바른 파라미터로 호출되었는지 확인
    mock_llm_service.generate_completion.assert_called_once()
    call_args = mock_llm_service.generate_completion.call_args
    messages = call_args.kwargs["messages"]
    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert "고객 상담 어시스턴트" in messages[0]["content"]
    assert messages[1]["role"] == "user"
    assert messages[1]["content"] == "상품 문의 드립니다"
    assert call_args.kwargs["temperature"] == 0.7
    assert call_args.kwargs["max_output_tokens"] == 500


@pytest.mark.asyncio
async def test_start_conversation_handles_llm_failure_with_fallback(
    conversation_repository: ConversationRepository,
):
    """Test that LLM failures result in fallback message."""
    # Arrange
    mock_llm_service = AsyncMock(spec=LLMService)
    mock_llm_service.generate_completion = AsyncMock(
        side_effect=Exception("OpenAI API error")
    )

    service = ConversationService(
        repository=conversation_repository,
        llm_service=mock_llm_service,
    )

    customer_id = uuid4()
    payload = StartConversationRequest(
        customer_id=customer_id,
        message=MessagePayload(body="테스트 메시지", attachments=[]),
    )

    # Act
    response = await service.start_conversation(payload)

    # Assert
    assert len(response.messages) == 2
    ai_msg = response.messages[1]
    assert ai_msg.sender_type == "ai"
    assert "일시적인 오류" in ai_msg.body
    assert "상담원 연결" in ai_msg.body


@pytest.mark.asyncio
async def test_start_conversation_assigns_correct_sequence_numbers(
    conversation_service: ConversationService,
):
    """Test that messages have correct sequence numbers."""
    # Arrange
    payload = StartConversationRequest(
        customer_id=uuid4(),
        message=MessagePayload(body="순서 테스트", attachments=[]),
    )

    # Act
    response = await conversation_service.start_conversation(payload)

    # Assert
    sequences = [msg.sequence for msg in response.messages]
    assert sequences == [1, 2]


@pytest.mark.asyncio
async def test_start_conversation_stores_ai_message_in_repository(
    conversation_service: ConversationService,
    conversation_repository: ConversationRepository,
):
    """Test that AI message is persisted in repository."""
    # Arrange
    customer_id = uuid4()
    payload = StartConversationRequest(
        customer_id=customer_id,
        message=MessagePayload(body="저장 테스트", attachments=[]),
    )

    # Act
    response = await conversation_service.start_conversation(payload)
    conversation_id = response.conversation.id

    # Assert - 저장소에서 메시지 확인
    stored_messages = conversation_repository._messages.get(conversation_id, [])
    assert len(stored_messages) == 2
    assert stored_messages[0].sender_type == "customer"
    assert stored_messages[1].sender_type == "ai"


@pytest.mark.asyncio
async def test_start_conversation_with_organization_id(
    conversation_service: ConversationService,
):
    """Test conversation creation with organization ID."""
    # Arrange
    org_id = uuid4()
    customer_id = uuid4()
    payload = StartConversationRequest(
        organization_id=org_id,
        customer_id=customer_id,
        message=MessagePayload(body="조직 테스트", attachments=[]),
    )

    # Act
    response = await conversation_service.start_conversation(payload)

    # Assert
    assert response.conversation.organization_id == org_id


@pytest.mark.asyncio
async def test_start_conversation_pending_approval_defaults_to_false(
    conversation_service: ConversationService,
):
    """Test that pending_approval is False (HITL not yet implemented)."""
    # Arrange
    payload = StartConversationRequest(
        customer_id=uuid4(),
        message=MessagePayload(body="승인 테스트", attachments=[]),
    )

    # Act
    response = await conversation_service.start_conversation(payload)

    # Assert
    assert response.pending_approval is False
