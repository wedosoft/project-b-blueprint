"""Insert sample documents into Qdrant for testing RAG integration.

Usage (from repository root):
```bash
cd backend && source venv/bin/activate && PYTHONPATH=/Users/alan/GitHub/project-b-blueprint python ../scripts/insert_sample_documents.py
```
"""

import asyncio
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "backend"))

# Set environment to load .env from project root
os.chdir(project_root)

from openai import AsyncOpenAI
from app.services.qdrant_service import QdrantService
from core.config import get_settings


async def main():
    """Insert sample Korean customer service documents for testing."""
    settings = get_settings()

    # Initialize services
    openai_api_key = settings.llm.require_api_key().get_secret_value()
    openai_client = AsyncOpenAI(api_key=openai_api_key)
    qdrant_service = QdrantService(settings=settings, openai_client=openai_client)

    # Ensure collection exists
    qdrant_service.ensure_collection_exists()

    # Use consistent organization ID for testing
    test_org_id = "550e8400-e29b-41d4-a716-446655440000"

    # Sample Korean customer service documents
    sample_documents = [
        {
            "id": "doc-001",
            "content": """문의: 배송이 언제 도착하나요?

답변: 안녕하세요. 배송은 주문 후 3-5일 이내에 도착합니다.
주문 번호를 알려주시면 정확한 배송 상태를 확인해드리겠습니다.
빠른 시일 내에 받아보실 수 있도록 최선을 다하겠습니다.""",
            "metadata": {
                "doc_type": "customer_service",
                "category": "배송문의",
                "organization_id": test_org_id,
                "tags": "배송,주문,도착시간"
            }
        },
        {
            "id": "doc-002",
            "content": """문의: 환불은 어떻게 진행되나요?

답변: 환불은 다음과 같이 진행됩니다:
1. 고객센터에 환불 요청
2. 상품 반송 (배송비는 고객 부담)
3. 상품 확인 후 3-5일 이내 환불 처리

환불은 원래 결제 수단으로 처리되며, 영업일 기준 3-5일 소요됩니다.""",
            "metadata": {
                "doc_type": "customer_service",
                "category": "환불문의",
                "organization_id": test_org_id,
                "tags": "환불,반품,결제취소"
            }
        },
        {
            "id": "doc-003",
            "content": """문의: 제품 사용 방법을 알려주세요.

답변: 제품 사용 방법은 다음과 같습니다:
1. 포장을 개봉하고 모든 구성품을 확인하세요
2. 사용 설명서를 참고하여 초기 설정을 진행하세요
3. 전원을 켜고 기본 기능을 테스트하세요

자세한 사용법은 제품과 함께 제공된 설명서 또는
웹사이트의 FAQ 섹션을 참고해주세요.""",
            "metadata": {
                "doc_type": "customer_service",
                "category": "사용방법",
                "organization_id": test_org_id,
                "tags": "사용법,설명서,초기설정"
            }
        },
        {
            "id": "doc-004",
            "content": """문의: 회원 가입은 어떻게 하나요?

답변: 회원 가입 절차:
1. 홈페이지 상단의 '회원가입' 버튼 클릭
2. 이메일 주소와 비밀번호 입력
3. 본인 인증 (휴대폰 또는 이메일)
4. 약관 동의 후 가입 완료

가입하시면 다양한 혜택과 할인을 받으실 수 있습니다.""",
            "metadata": {
                "doc_type": "customer_service",
                "category": "회원가입",
                "organization_id": test_org_id,
                "tags": "회원가입,계정생성,인증"
            }
        },
        {
            "id": "doc-005",
            "content": """문의: 비밀번호를 잊어버렸어요.

답변: 비밀번호 재설정 방법:
1. 로그인 페이지에서 '비밀번호 찾기' 클릭
2. 가입 시 등록한 이메일 주소 입력
3. 이메일로 전송된 재설정 링크 클릭
4. 새 비밀번호 입력 및 확인

이메일이 오지 않으면 스팸함을 확인하시거나
고객센터(1588-0000)로 문의해주세요.""",
            "metadata": {
                "doc_type": "customer_service",
                "category": "계정문의",
                "organization_id": test_org_id,
                "tags": "비밀번호,계정복구,로그인"
            }
        },
        {
            "id": "doc-006",
            "content": """문의: 할인 쿠폰은 어떻게 사용하나요?

답변: 쿠폰 사용 방법:
1. 장바구니에서 상품 확인
2. 결제 단계에서 '쿠폰 사용' 선택
3. 보유한 쿠폰 목록에서 사용할 쿠폰 선택
4. 할인이 적용된 금액 확인 후 결제

쿠폰은 유효기간과 최소 주문 금액 조건이 있으니
사용 전 확인해주세요.""",
            "metadata": {
                "doc_type": "customer_service",
                "category": "쿠폰/할인",
                "organization_id": test_org_id,
                "tags": "쿠폰,할인,프로모션"
            }
        },
        {
            "id": "doc-007",
            "content": """문의: 제품이 불량인 것 같아요.

답변: 불량 제품 처리 절차:
1. 고객센터(1588-0000)로 연락하여 불량 증상 설명
2. 제품 사진 또는 동영상 전송 (이메일 또는 카톡)
3. 불량 확인 후 교환 또는 환불 진행
4. 택배 수거 또는 교환 제품 발송

제품 수령 후 7일 이내 불량 신고 시 무료 교환/환불이
가능합니다.""",
            "metadata": {
                "doc_type": "customer_service",
                "category": "불량/교환",
                "organization_id": test_org_id,
                "tags": "불량품,교환,AS"
            }
        },
        {
            "id": "doc-008",
            "content": """문의: 배송지 변경이 가능한가요?

답변: 배송지 변경 가능 여부:
- 주문 후 배송 준비 중: 변경 가능 (고객센터 연락)
- 배송 중: 택배사 고객센터로 직접 연락하여 변경
- 배송 완료: 변경 불가

배송지 변경은 최대한 빨리 연락주시는 것이 좋습니다.
마이페이지에서 주문 상태를 확인하실 수 있습니다.""",
            "metadata": {
                "doc_type": "customer_service",
                "category": "배송문의",
                "organization_id": test_org_id,
                "tags": "배송지변경,주소수정,배송"
            }
        }
    ]

    print(f"📦 Inserting {len(sample_documents)} sample documents...")

    # Insert documents
    for doc in sample_documents:
        try:
            await qdrant_service.upsert_document(
                document_id=doc["id"],
                content=doc["content"],
                metadata=doc["metadata"]
            )
            print(f"✅ Inserted: {doc['id']} - {doc['metadata']['category']}")
        except Exception as exc:
            print(f"❌ Failed to insert {doc['id']}: {exc}")

    print(f"\n🎉 Successfully inserted {len(sample_documents)} documents into Qdrant!")
    print(f"Collection: {settings.qdrant.collection}")
    print(f"Dimension: {settings.qdrant.vector_dimension}")

    # Test search
    print("\n🔍 Testing vector search...")
    query = "배송이 언제 오나요?"
    print(f"Query: {query}")

    results = await qdrant_service.search_similar(
        query_text=query,
        limit=3,
        score_threshold=0.3,
        organization_id=test_org_id
    )

    print(f"\n📊 Found {len(results)} similar documents:")
    for i, result in enumerate(results, 1):
        print(f"\n{i}. Score: {result.score:.4f}")
        print(f"   Category: {result.metadata.get('category', 'N/A')}")
        print(f"   Preview: {result.content[:100]}...")

    # Cleanup
    await qdrant_service.close()
    print("\n✨ Test completed successfully!")


if __name__ == "__main__":
    asyncio.run(main())
