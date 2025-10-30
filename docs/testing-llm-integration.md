# LLM 통합 테스트 가이드

## 환경 변수 설정

프로젝트 루트의 `.env` 파일에 OpenAI API 키가 이미 설정되어 있습니다:
```bash
# /Users/alan/GitHub/project-b-blueprint/.env
OPENAI_API_KEY="sk-proj-..."
```

백엔드가 자동으로 이 파일을 로드합니다 (`backend/core/config/__init__.py` line 13-14).

## 테스트 방법

### 1. 유닛 테스트 (모킹 사용)

LLM 호출을 모킹하여 빠르고 비용 없이 테스트:

```bash
cd backend
python3 -m pytest tests/unit/test_conversation_service.py -v
```

**실행 결과:**
- ✅ 6개 테스트 모두 통과
- ⚡ 실제 API 호출 없음 (비용 0원)
- 🚀 빠른 실행 (< 1초)

### 2. 통합 테스트 (실제 API 사용)

실제 OpenAI API를 호출하여 end-to-end 테스트를 작성할 수 있습니다.

#### 통합 테스트 파일 생성

`backend/tests/integration/test_llm_integration.py`:

```python
"""Integration tests for LLM service with real OpenAI API."""

import pytest
from app.services.llm_service import LLMService

@pytest.mark.integration
@pytest.mark.asyncio
async def test_llm_service_real_api():
    """Test LLM service with actual OpenAI API call."""
    # Arrange
    service = LLMService()
    messages = [
        {"role": "system", "content": "당신은 친절한 상담원입니다."},
        {"role": "user", "content": "안녕하세요"}
    ]

    # Act
    result = await service.generate_completion(
        messages=messages,
        temperature=0.7,
        max_output_tokens=100
    )

    # Assert
    assert result.provider == "openai"
    assert result.content  # 응답이 있어야 함
    assert len(result.content) > 0
    assert result.usage is not None
    assert result.usage.total_tokens > 0
    print(f"\\n✅ AI Response: {result.content}")
    print(f"💰 Tokens used: {result.usage.total_tokens}")
```

#### 실행 방법

```bash
# 통합 테스트만 실행 (실제 API 호출, 비용 발생)
cd backend
python3 -m pytest tests/integration/test_llm_integration.py -v -m integration

# 특정 테스트만 실행
python3 -m pytest tests/integration/test_llm_integration.py::test_llm_service_real_api -v -s
```

**주의:** 실제 API를 호출하므로 비용이 발생합니다!

### 3. API 엔드포인트 테스트 (실제 서버)

백엔드 서버를 실행하고 실제 API를 호출하여 테스트:

#### 서버 실행

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### cURL로 테스트

```bash
# POST /v1/conversations 호출
curl -X POST http://localhost:8000/v1/conversations \\
  -H "Content-Type: application/json" \\
  -d '{
    "customerId": "00000000-0000-0000-0000-000000000001",
    "message": {
      "body": "상품 문의 드립니다",
      "attachments": []
    },
    "metadata": {
      "source": "web"
    }
  }'
```

#### Python requests로 테스트

```python
import requests
import json

url = "http://localhost:8000/v1/conversations"
payload = {
    "customerId": "00000000-0000-0000-0000-000000000001",
    "message": {
        "body": "배송 문의드립니다. 언제 도착하나요?",
        "attachments": []
    }
}

response = requests.post(url, json=payload)
data = response.json()

print("✅ Conversation created!")
print(f"📝 Messages: {len(data['messages'])}")
print(f"👤 Customer: {data['messages'][0]['body']}")
print(f"🤖 AI: {data['messages'][1]['body']}")
```

### 4. httpx를 사용한 통합 테스트

FastAPI TestClient를 사용하여 서버 실행 없이 API 테스트:

```python
"""Integration test with real LLM but no server startup."""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

@pytest.mark.integration
def test_conversation_api_with_real_llm():
    """Test full conversation flow with real OpenAI API."""
    payload = {
        "customerId": "00000000-0000-0000-0000-000000000001",
        "message": {
            "body": "주문 취소하고 싶습니다",
            "attachments": []
        }
    }

    response = client.post("/v1/conversations", json=payload)

    assert response.status_code == 201
    data = response.json()

    # 고객 메시지와 AI 응답이 모두 있어야 함
    assert len(data["messages"]) == 2
    assert data["messages"][0]["senderType"] == "customer"
    assert data["messages"][1]["senderType"] == "ai"

    # AI 응답 내용 확인
    ai_response = data["messages"][1]["body"]
    assert len(ai_response) > 0
    print(f"\\n🤖 AI Response: {ai_response}")
```

## 테스트 비용 관리

### 모킹 테스트 (권장)
- ✅ 비용: 0원
- ✅ 속도: 빠름
- ✅ 용도: 로직 검증, CI/CD

### 통합 테스트 (선택적)
- 💰 비용: 발생 (GPT-4: ~$0.01/1K tokens)
- ⏱️ 속도: 느림 (API 응답 대기)
- 🎯 용도: 실제 품질 검증, 프롬프트 테스트

### pytest 마커 활용

```bash
# 모킹 테스트만 (기본)
pytest tests/unit/

# 통합 테스트만 (비용 발생 주의)
pytest -m integration

# 통합 테스트 제외
pytest -m "not integration"
```

## 환경별 설정

### 개발 환경
```bash
# .env
OPENAI_API_KEY="sk-proj-..."  # 개발용 키
LLM_PROVIDER="openai"
```

### CI/CD 환경
```bash
# 실제 API 호출 없이 테스트
pytest -m "not integration"

# 또는 mock API key 사용
OPENAI_API_KEY="test-key" pytest tests/unit/
```

### 프로덕션 환경
```bash
# .env (환경 변수로 주입)
OPENAI_API_KEY="${OPENAI_API_KEY}"  # 시크릿 관리 도구에서 주입
LLM_PROVIDER="openai"
```

## 트러블슈팅

### 1. "Missing required environment variable: OPENAI_API_KEY"

**원인:** `.env` 파일이 로드되지 않음

**해결:**
```bash
# 프로젝트 루트에서 실행
cd /Users/alan/GitHub/project-b-blueprint
python3 -m pytest backend/tests/unit/ -v

# 또는 backend 디렉토리에서
cd backend
python3 -m pytest tests/unit/ -v
```

### 2. "AsyncOpenAI() missing 1 required argument: 'api_key'"

**원인:** API 키가 None

**해결:** `.env` 파일에 올바른 API 키 설정 확인
```bash
cat .env | grep OPENAI_API_KEY
```

### 3. 실제 API 호출 시 RateLimitError

**원인:** API 호출 제한 초과

**해결:**
- Retry 로직 이미 구현됨 (max_retries=2)
- 테스트 간 sleep 추가
- pytest-xdist로 병렬 실행 제한

## 다음 단계

✅ Task 1 완료 - LLM 통합
🔄 Task 2 진행 중 - Qdrant 벡터 검색 통합
⏳ Task 3 대기 중 - HITL 승인 UI

Task 2와 Task 3는 병렬로 진행 가능합니다!
