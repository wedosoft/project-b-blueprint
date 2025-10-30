"""Test RAG integration with conversation API.

Usage:
```bash
# Terminal 1: Start server
cd backend && source venv/bin/activate && uvicorn app.main:app --reload

# Terminal 2: Run this test
cd backend && source venv/bin/activate && python ../scripts/test_rag_api.py
```
"""

import asyncio
import httpx


async def test_conversation_with_rag():
    """Test conversation API with RAG context injection."""

    base_url = "http://localhost:8000"

    # Use valid UUID for organization (can be any UUID for testing)
    test_org_id = "550e8400-e29b-41d4-a716-446655440000"

    # Test queries that should match our sample documents
    test_cases = [
        {
            "query": "배송이 언제 도착하나요? 주문 번호는 ABC123입니다.",
            "expected_context": "주문 후 3-5일",
        },
        {
            "query": "환불을 받고 싶은데 어떻게 해야 하나요?",
            "expected_context": "환불",
        },
        {
            "query": "비밀번호가 기억나지 않아요.",
            "expected_context": "비밀번호 찾기",
        },
    ]

    async with httpx.AsyncClient(timeout=60.0) as client:
        for i, test in enumerate(test_cases, 1):
            print(f"\n{'='*80}")
            print(f"Test {i}: {test['query']}")
            print(f"{'='*80}")

            payload = {
                "organizationId": test_org_id,
                "message": {
                    "body": test["query"]
                }
            }

            try:
                response = await client.post(
                    f"{base_url}/v1/conversations",
                    json=payload
                )

                if response.status_code in [200, 201]:
                    data = response.json()
                    conversation_id = data['conversation']['id']
                    print(f"✅ Success! Conversation ID: {conversation_id}")

                    # Get the AI response
                    ai_message = next(
                        (msg for msg in data['messages'] if msg['senderType'] == 'ai'),
                        None
                    )

                    if ai_message:
                        print(f"\n🤖 AI Response:")
                        print(f"{ai_message['body']}")

                        # Check if expected context appears in response
                        if test['expected_context'].lower() in ai_message['body'].lower():
                            print(f"\n✅ Response contains expected context: '{test['expected_context']}'")
                        else:
                            print(f"\n⚠️  Response may not contain expected context: '{test['expected_context']}'")
                    else:
                        print("❌ No AI response found in conversation")
                else:
                    print(f"❌ Error: {response.status_code}")
                    print(response.text)

            except Exception as exc:
                print(f"❌ Request failed: {exc}")

            await asyncio.sleep(2)  # Rate limiting

    print(f"\n{'='*80}")
    print("✨ RAG Integration Test Completed!")
    print(f"{'='*80}")


if __name__ == "__main__":
    asyncio.run(test_conversation_with_rag())
