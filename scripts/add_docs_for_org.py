"""Add sample documents for a specific organization ID.

Usage:
```bash
cd backend
source venv/bin/activate
python ../scripts/add_docs_for_org.py <organization-id>
```

Example:
```bash
python ../scripts/add_docs_for_org.py 3fa85f64-5717-4562-b3fc-2c963f66afa6
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
os.chdir(project_root)

from openai import AsyncOpenAI
from app.services.qdrant_service import QdrantService
from core.config import get_settings


async def main():
    """Insert sample documents for specified organization."""
    if len(sys.argv) < 2:
        print("Usage: python add_docs_for_org.py <organization-id>")
        print("Example: python add_docs_for_org.py 3fa85f64-5717-4562-b3fc-2c963f66afa6")
        sys.exit(1)

    org_id = sys.argv[1]
    print(f"Adding documents for organization: {org_id}\n")

    settings = get_settings()

    # Initialize services
    openai_api_key = settings.llm.require_api_key().get_secret_value()
    openai_client = AsyncOpenAI(api_key=openai_api_key)
    qdrant_service = QdrantService(settings=settings, openai_client=openai_client)

    # Sample documents
    sample_documents = [
        {
            "id": f"doc-{org_id}-001",
            "content": """문의: 배송이 언제 도착하나요?

답변: 안녕하세요. 배송은 주문 후 3-5일 이내에 도착합니다.
주문 번호를 알려주시면 정확한 배송 상태를 확인해드리겠습니다.
빠른 시일 내에 받아보실 수 있도록 최선을 다하겠습니다.""",
            "metadata": {
                "doc_type": "customer_service",
                "category": "배송문의",
                "organization_id": org_id,
                "tags": "배송,주문,도착시간"
            }
        },
        {
            "id": f"doc-{org_id}-002",
            "content": """문의: 환불은 어떻게 진행되나요?

답변: 환불은 다음과 같이 진행됩니다:
1. 고객센터에 환불 요청
2. 상품 반송 (배송비는 고객 부담)
3. 상품 확인 후 3-5일 이내 환불 처리

환불은 원래 결제 수단으로 처리되며, 영업일 기준 3-5일 소요됩니다.""",
            "metadata": {
                "doc_type": "customer_service",
                "category": "환불문의",
                "organization_id": org_id,
                "tags": "환불,반품,결제취소"
            }
        },
        {
            "id": f"doc-{org_id}-003",
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
                "organization_id": org_id,
                "tags": "비밀번호,계정복구,로그인"
            }
        },
    ]

    print(f"📦 Inserting {len(sample_documents)} sample documents...\n")

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

    print(f"\n🎉 Successfully inserted {len(sample_documents)} documents!")

    # Test search
    print(f"\n🔍 Testing vector search for org: {org_id}...")
    query = "환불하고 싶어요"
    print(f"Query: {query}\n")

    results = await qdrant_service.search_similar(
        query_text=query,
        limit=3,
        score_threshold=0.3,
        organization_id=org_id
    )

    print(f"📊 Found {len(results)} similar documents:")
    for i, result in enumerate(results, 1):
        print(f"\n{i}. Score: {result.score:.4f}")
        print(f"   Category: {result.metadata.get('category', 'N/A')}")
        print(f"   Preview: {result.content[:80]}...")

    await qdrant_service.close()
    print("\n✨ Done!")


if __name__ == "__main__":
    asyncio.run(main())
