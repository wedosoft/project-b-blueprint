# API 테스트 가이드 (curl)

## 🚀 서버 시작

```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

서버가 시작되면 다음 메시지가 표시됩니다:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Application startup complete.
```

## 1️⃣ Health Check (루트 경로)

```bash
curl http://localhost:8000/
```

**응답**:
```json
{
  "status": "ok",
  "service": "AI Contact Center API",
  "version": "0.1.0"
}
```

## 2️⃣ API 문서 확인

브라우저에서 열기:
```
http://localhost:8000/docs
```

Swagger UI에서 모든 API 엔드포인트를 확인하고 테스트할 수 있습니다.

## 3️⃣ 대화 시작 (RAG 포함)

### 테스트 1: 배송 문의

```bash
curl -X POST http://localhost:8000/v1/conversations \
  -H "Content-Type: application/json" \
  -d '{
    "organizationId": "550e8400-e29b-41d4-a716-446655440000",
    "message": {
      "body": "배송이 언제 도착하나요? 주문 번호는 ABC123입니다."
    }
  }'
```

**예상 응답** (RAG 컨텍스트 포함):
```json
{
  "conversation": {
    "id": "uuid-here",
    "organizationId": "550e8400-e29b-41d4-a716-446655440000",
    "status": "active",
    "channel": "text-web",
    "priority": "standard"
  },
  "messages": [
    {
      "id": "msg-uuid-1",
      "senderType": "customer",
      "body": "배송이 언제 도착하나요? 주문 번호는 ABC123입니다.",
      "sequence": 1
    },
    {
      "id": "msg-uuid-2",
      "senderType": "ai",
      "body": "안녕하세요. 주문 번호 ABC123의 배송 상태를 확인해보겠습니다.\n\n일반적으로 배송은 주문 후 3-5일 이내에 도착합니다...",
      "sequence": 2
    }
  ],
  "pendingApproval": false
}
```

✅ **확인 포인트**: AI 응답에 "주문 후 3-5일"이 포함되어 있으면 RAG가 정상 작동하는 것입니다!

### 테스트 2: 환불 문의

```bash
curl -X POST http://localhost:8000/v1/conversations \
  -H "Content-Type: application/json" \
  -d '{
    "organizationId": "550e8400-e29b-41d4-a716-446655440000",
    "message": {
      "body": "환불을 받고 싶은데 어떻게 해야 하나요?"
    }
  }'
```

✅ **확인 포인트**: "환불 절차", "3-5일 이내", "배송비는 고객 부담" 등이 포함됨

### 테스트 3: 비밀번호 분실

```bash
curl -X POST http://localhost:8000/v1/conversations \
  -H "Content-Type: application/json" \
  -d '{
    "organizationId": "550e8400-e29b-41d4-a716-446655440000",
    "message": {
      "body": "비밀번호가 기억나지 않아요."
    }
  }'
```

✅ **확인 포인트**: "비밀번호 찾기", "이메일 주소 입력", "재설정 링크" 등이 포함됨

### 테스트 4: 쿠폰 사용법

```bash
curl -X POST http://localhost:8000/v1/conversations \
  -H "Content-Type: application/json" \
  -d '{
    "organizationId": "550e8400-e29b-41d4-a716-446655440000",
    "message": {
      "body": "쿠폰은 어떻게 사용하나요?"
    }
  }'
```

✅ **확인 포인트**: "장바구니", "결제 단계", "쿠폰 선택" 등이 포함됨

## 4️⃣ 응답 보기 좋게 포맷팅 (jq 사용)

jq가 설치되어 있다면:

```bash
curl -X POST http://localhost:8000/v1/conversations \
  -H "Content-Type: application/json" \
  -d '{
    "organizationId": "550e8400-e29b-41d4-a716-446655440000",
    "message": {
      "body": "배송이 언제 도착하나요?"
    }
  }' | jq .
```

AI 응답만 추출:

```bash
curl -s -X POST http://localhost:8000/v1/conversations \
  -H "Content-Type: application/json" \
  -d '{
    "organizationId": "550e8400-e29b-41d4-a716-446655440000",
    "message": {
      "body": "배송이 언제 도착하나요?"
    }
  }' | jq -r '.messages[] | select(.senderType == "ai") | .body'
```

## 5️⃣ RAG 동작 확인 방법

### RAG가 작동하는지 확인하는 방법:

1. **Qdrant 없이 테스트** (RAG 비활성화)
   - QdrantService를 None으로 설정하면 컨텍스트 없이 응답
   - 일반적인 답변만 제공

2. **Qdrant 있이 테스트** (RAG 활성화, 현재 상태)
   - 샘플 문서에서 검색된 구체적인 정보 포함
   - "주문 후 3-5일", "고객센터(1588-0000)" 등 구체적 내용

### 비교 예시:

**RAG 없음**:
> "배송 시간은 상품과 배송지에 따라 다릅니다. 주문 내역에서 확인하실 수 있습니다."

**RAG 있음** (현재):
> "일반적으로 배송은 **주문 후 3-5일 이내**에 도착합니다. 주문 번호를 알려주시면 정확한 배송 상태를 확인해드리겠습니다."

## 6️⃣ 다양한 조직 테스트

다른 organization_id로 테스트 (문서가 없어서 RAG 컨텍스트 없음):

```bash
curl -X POST http://localhost:8000/v1/conversations \
  -H "Content-Type: application/json" \
  -d '{
    "organizationId": "00000000-0000-0000-0000-000000000000",
    "message": {
      "body": "배송이 언제 도착하나요?"
    }
  }'
```

✅ **확인 포인트**: 일반적인 답변만 제공 (구체적인 "3-5일" 언급 없음)

## 7️⃣ 에러 케이스 테스트

### 잘못된 organization_id (UUID 아님)

```bash
curl -X POST http://localhost:8000/v1/conversations \
  -H "Content-Type: application/json" \
  -d '{
    "organizationId": "invalid-uuid",
    "message": {
      "body": "테스트"
    }
  }'
```

**응답**: 422 Validation Error

### message 필드 누락

```bash
curl -X POST http://localhost:8000/v1/conversations \
  -H "Content-Type: application/json" \
  -d '{
    "organizationId": "550e8400-e29b-41d4-a716-446655440000"
  }'
```

**응답**: 422 Validation Error

## 8️⃣ 빠른 테스트 스크립트

모든 테스트를 한번에 실행:

```bash
#!/bin/bash

ORG_ID="550e8400-e29b-41d4-a716-446655440000"
BASE_URL="http://localhost:8000"

echo "=== Test 1: 배송 문의 ==="
curl -s -X POST $BASE_URL/v1/conversations \
  -H "Content-Type: application/json" \
  -d "{\"organizationId\":\"$ORG_ID\",\"message\":{\"body\":\"배송이 언제 도착하나요?\"}}" \
  | jq -r '.messages[] | select(.senderType == "ai") | .body'

echo -e "\n=== Test 2: 환불 문의 ==="
curl -s -X POST $BASE_URL/v1/conversations \
  -H "Content-Type: application/json" \
  -d "{\"organizationId\":\"$ORG_ID\",\"message\":{\"body\":\"환불하고 싶어요\"}}" \
  | jq -r '.messages[] | select(.senderType == "ai") | .body'

echo -e "\n=== Test 3: 비밀번호 분실 ==="
curl -s -X POST $BASE_URL/v1/conversations \
  -H "Content-Type: application/json" \
  -d "{\"organizationId\":\"$ORG_ID\",\"message\":{\"body\":\"비밀번호를 잊어버렸어요\"}}" \
  | jq -r '.messages[] | select(.senderType == "ai") | .body'
```

이 스크립트를 `scripts/quick-test.sh`로 저장하고 실행:

```bash
chmod +x scripts/quick-test.sh
./scripts/quick-test.sh
```

## 🔍 문제 해결

### 서버가 시작되지 않는 경우

1. 가상환경 활성화 확인:
   ```bash
   which python  # backend/venv/bin/python 이어야 함
   ```

2. 의존성 설치 확인:
   ```bash
   cd backend
   pip install -r requirements.txt  # 또는 pyproject.toml 사용
   ```

3. 환경변수 확인:
   ```bash
   cat .env  # OPENAI_API_KEY, QDRANT_URL, QDRANT_API_KEY 확인
   ```

### RAG가 작동하지 않는 경우

1. Qdrant 문서 확인:
   ```bash
   cd backend
   source venv/bin/activate
   python ../scripts/test_vector_search.py
   ```

2. Qdrant 컬렉션 재생성:
   ```bash
   cd backend
   source venv/bin/activate
   PYTHONPATH=/Users/alan/GitHub/project-b-blueprint python -m backend.infrastructure.embeddings.bootstrap_qdrant --force-recreate
   python ../scripts/insert_sample_documents.py
   ```

### 응답이 느린 경우

- OpenAI API 호출: ~2-4초
- Qdrant 검색: ~0.1-0.3초
- 총 응답 시간: ~2-5초 (정상)

---

**작성일**: 2025-10-30
**테스트 Organization ID**: `550e8400-e29b-41d4-a716-446655440000`
