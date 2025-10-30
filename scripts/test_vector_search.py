"""Test vector search with various queries and thresholds.

Usage:
```bash
cd backend && source venv/bin/activate && python ../scripts/test_vector_search.py
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
    """Test vector search with different queries and thresholds."""
    settings = get_settings()

    # Initialize services
    openai_api_key = settings.llm.require_api_key().get_secret_value()
    openai_client = AsyncOpenAI(api_key=openai_api_key)
    qdrant_service = QdrantService(settings=settings, openai_client=openai_client)

    # Test queries
    test_queries = [
        "배송이 언제 오나요?",
        "환불하고 싶어요",
        "비밀번호를 잊어버렸어요",
        "제품이 고장났어요",
        "쿠폰은 어떻게 사용하나요?",
    ]

    thresholds = [0.3, 0.5, 0.7]

    for query in test_queries:
        print(f"\n{'='*80}")
        print(f"🔍 Query: {query}")
        print(f"{'='*80}")

        for threshold in thresholds:
            results = await qdrant_service.search_similar(
                query_text=query,
                limit=3,
                score_threshold=threshold,
                organization_id="test-org-001"
            )

            print(f"\n📊 Threshold: {threshold} → Found {len(results)} results")
            for i, result in enumerate(results, 1):
                print(f"  {i}. Score: {result.score:.4f}")
                print(f"     Category: {result.metadata.get('category', 'N/A')}")
                print(f"     Tags: {result.metadata.get('tags', 'N/A')}")
                print(f"     Content preview: {result.content[:80]}...")

    # Test without organization filter
    print(f"\n\n{'='*80}")
    print("🌐 Testing without organization filter")
    print(f"{'='*80}")

    results = await qdrant_service.search_similar(
        query_text="배송 문의",
        limit=5,
        score_threshold=0.3,
        organization_id=None  # No filter
    )

    print(f"\n📊 Found {len(results)} results (no org filter, threshold=0.3)")
    for i, result in enumerate(results, 1):
        print(f"  {i}. Score: {result.score:.4f} | Category: {result.metadata.get('category', 'N/A')}")

    await qdrant_service.close()
    print("\n✨ Test completed!")


if __name__ == "__main__":
    asyncio.run(main())
