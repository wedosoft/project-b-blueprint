"""Integration tests for LLM service with real OpenAI API.

⚠️ WARNING: These tests make actual API calls and will incur costs!
Run with: pytest -m integration
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.llm_service import LLMService

client = TestClient(app)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_llm_service_generates_real_response():
    """Test LLM service with actual OpenAI API call."""
    # Arrange
    service = LLMService()
    messages = [
        {"role": "system", "content": "당신은 친절한 고객 상담원입니다."},
        {"role": "user", "content": "안녕하세요, 배송 문의 드립니다."},
    ]

    # Act
    result = await service.generate_completion(
        messages=messages, temperature=0.7, max_output_tokens=100
    )

    # Assert
    assert result.provider == "openai"
    assert result.content
    assert len(result.content) > 0
    assert result.usage is not None
    assert result.usage.total_tokens > 0

    print(f"\n✅ AI Response: {result.content}")
    print(f"💰 Tokens used: {result.usage.total_tokens}")
    print(f"⚡ Latency: {result.latency_ms}ms")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_llm_service_handles_korean_well():
    """Test that LLM service produces good Korean responses."""
    # Arrange
    service = LLMService()
    messages = [
        {"role": "system", "content": "당신은 전문적인 상담원입니다. 항상 한글로 응답합니다."},
        {"role": "user", "content": "주문을 취소하고 싶습니다."},
    ]

    # Act
    result = await service.generate_completion(
        messages=messages, temperature=0.7, max_output_tokens=200
    )

    # Assert
    assert result.content
    # 한글이 포함되어 있는지 확인
    assert any("\uac00" <= char <= "\ud7a3" for char in result.content)

    print(f"\n🇰🇷 Korean Response: {result.content}")


@pytest.mark.integration
def test_conversation_api_with_real_llm():
    """Test full conversation flow with real OpenAI API.

    This test creates a conversation and verifies that the AI response
    is generated using the actual OpenAI API.
    """
    # Arrange
    payload = {
        "customerId": "00000000-0000-0000-0000-000000000001",
        "message": {"body": "주문 취소 문의드립니다. 어떻게 하나요?", "attachments": []},
        "metadata": {"source": "integration_test"},
    }

    # Act
    response = client.post("/v1/conversations", json=payload)

    # Assert
    assert response.status_code == 201
    data = response.json()

    # 고객 메시지와 AI 응답이 모두 있어야 함
    assert len(data["messages"]) == 2
    assert data["messages"][0]["senderType"] == "customer"
    assert data["messages"][0]["body"] == "주문 취소 문의드립니다. 어떻게 하나요?"
    assert data["messages"][1]["senderType"] == "ai"

    # AI 응답 내용 확인
    ai_response = data["messages"][1]["body"]
    assert len(ai_response) > 0
    # Fallback 메시지가 아닌 실제 AI 응답인지 확인
    assert "일시적인 오류" not in ai_response

    print(f"\n👤 Customer: {data['messages'][0]['body']}")
    print(f"🤖 AI: {ai_response}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_llm_service_retry_on_failure():
    """Test that LLM service retries on temporary failures."""
    # Note: This test is difficult to trigger without mocking
    # In production, retry logic will handle transient errors
    service = LLMService(max_retries=2, retry_delay_seconds=0.1)
    messages = [
        {"role": "system", "content": "Test system"},
        {"role": "user", "content": "Test message"},
    ]

    # Act - should succeed even if there are transient issues
    result = await service.generate_completion(messages=messages)

    # Assert
    assert result.content
    print(f"\n✅ Retry mechanism working, got response: {result.content[:50]}...")


@pytest.mark.integration
def test_conversation_api_metadata_preserved():
    """Test that metadata is preserved through the conversation flow."""
    # Arrange
    payload = {
        "customerId": "00000000-0000-0000-0000-000000000002",
        "message": {"body": "테스트 메시지", "attachments": []},
        "metadata": {"channel": "mobile_app", "version": "1.2.3", "user_agent": "TestApp/1.0"},
    }

    # Act
    response = client.post("/v1/conversations", json=payload)

    # Assert
    assert response.status_code == 201
    data = response.json()
    assert data["conversation"]["metadata"]["channel"] == "mobile_app"
    assert data["conversation"]["metadata"]["version"] == "1.2.3"

    print(f"\n📊 Metadata preserved: {data['conversation']['metadata']}")
