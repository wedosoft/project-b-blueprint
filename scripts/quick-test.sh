#!/bin/bash

# RAG API 빠른 테스트 스크립트
# 사용법: ./scripts/quick-test.sh

ORG_ID="550e8400-e29b-41d4-a716-446655440000"
BASE_URL="http://localhost:8000"

# 색상 정의
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}===========================================${NC}"
echo -e "${BLUE}   AI Contact Center RAG API 테스트${NC}"
echo -e "${BLUE}===========================================${NC}\n"

# Health Check
echo -e "${GREEN}=== Health Check ===${NC}"
curl -s $BASE_URL/ | jq .
echo ""

# Test 1: 배송 문의
echo -e "${GREEN}=== Test 1: 배송 문의 ===${NC}"
echo "Query: 배송이 언제 도착하나요?"
curl -s -X POST $BASE_URL/v1/conversations \
  -H "Content-Type: application/json" \
  -d "{\"organizationId\":\"$ORG_ID\",\"message\":{\"body\":\"배송이 언제 도착하나요?\"}}" \
  | jq -r '.messages[] | select(.senderType == "ai") | .body'
echo ""

# Test 2: 환불 문의
echo -e "${GREEN}=== Test 2: 환불 문의 ===${NC}"
echo "Query: 환불하고 싶어요"
curl -s -X POST $BASE_URL/v1/conversations \
  -H "Content-Type: application/json" \
  -d "{\"organizationId\":\"$ORG_ID\",\"message\":{\"body\":\"환불하고 싶어요\"}}" \
  | jq -r '.messages[] | select(.senderType == "ai") | .body'
echo ""

# Test 3: 비밀번호 분실
echo -e "${GREEN}=== Test 3: 비밀번호 분실 ===${NC}"
echo "Query: 비밀번호를 잊어버렸어요"
curl -s -X POST $BASE_URL/v1/conversations \
  -H "Content-Type: application/json" \
  -d "{\"organizationId\":\"$ORG_ID\",\"message\":{\"body\":\"비밀번호를 잊어버렸어요\"}}" \
  | jq -r '.messages[] | select(.senderType == "ai") | .body'
echo ""

# Test 4: 쿠폰 사용
echo -e "${GREEN}=== Test 4: 쿠폰 사용 ===${NC}"
echo "Query: 쿠폰은 어떻게 사용하나요?"
curl -s -X POST $BASE_URL/v1/conversations \
  -H "Content-Type: application/json" \
  -d "{\"organizationId\":\"$ORG_ID\",\"message\":{\"body\":\"쿠폰은 어떻게 사용하나요?\"}}" \
  | jq -r '.messages[] | select(.senderType == "ai") | .body'
echo ""

echo -e "${BLUE}===========================================${NC}"
echo -e "${BLUE}   테스트 완료!${NC}"
echo -e "${BLUE}===========================================${NC}"
