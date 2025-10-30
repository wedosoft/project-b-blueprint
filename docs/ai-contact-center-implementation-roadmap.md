# AI Contact Center PoC - 구현 로드맵

**작성일**: 2025-10-30
**분석 기준**: `specs/001-ai-contact-center-mvp/plan.md` Progress Log

## 📊 현재 상태 분석

### ✅ 완료된 작업
- **POST `/v1/conversations` API**: FastAPI 라우트, 인메모리 저장소, Pydantic 스키마
- **ChatPanel UI**: Chakra UI 기반 고객 채팅 입력 인터페이스
- **LLM Service**: OpenAI GPT-4 통합 완료 (`llm_service.py`)
- **테스트 인프라**: Schemathesis 계약 테스트, Frontend 유닛 테스트
- **백엔드 설정**: 환경 변수, 테스트 환경 구성

### ⏳ 미완료 작업
1. ❌ LLM과 대화 API 완전 통합 (LLM Service는 구현되었으나 conversation API와 미연결)
2. ❌ Qdrant 벡터 검색 통합
3. ❌ HITL 승인 UI
4. ❌ 실시간 대시보드
5. ❌ Supabase Realtime 연동

## 🎯 우선순위 분석

### 전략: 순차적 가치 제공
"AI 응답 생성 → 품질 향상 → 품질 보증 → 실시간 협업 → 운영 모니터링"

| 순위 | 작업 | 이유 | 예상 기간 | 의존성 |
|------|------|------|-----------|--------|
| **1** | LLM과 대화 API 완전 통합 | 이미 구현된 LLM Service 활용으로 즉시 AI 응답 제공 가능 | 2-3일 | 없음 |
| **2** | Qdrant 벡터 검색 통합 | RAG 패턴으로 AI 응답 정확도 향상 | 4-5일 | Task 1 |
| **3** | HITL 승인 UI | AI 응답 품질 보증 메커니즘, 비즈니스 리스크 완화 | 5-6일 | Task 1 |
| **4** | Supabase Realtime 연동 | 실시간 협업 인프라, HITL과 대시보드 동기화 | 3-4일 | Task 3 |
| **5** | 실시간 대시보드 | 감독자 모니터링, 운영 가시성 제공 | 4-5일 | Task 4 |

**총 예상 기간**: 14-18일 (병렬 실행 고려 시)

---

## 📋 Task 1: LLM과 대화 API 완전 통합 [P1]

### 목표
기존 LLM Service를 `conversation_service.py`에 통합하여 POST `/v1/conversations` 호출 시 AI 응답 자동 생성

### 구현 단계
1. ✅ **ConversationService에 LLMService 의존성 주입**
   - 파일: `backend/app/services/conversation_service.py`
   - DI 컨테이너 또는 생성자 주입 패턴 적용

2. ✅ **start_conversation 메서드에서 AI 응답 생성**
   - 고객 메시지를 LLM에 전달
   - 시스템 프롬프트 구성 (고객 상담 어시스턴트 역할)
   - LLM 호출 및 응답 수신

3. ✅ **생성된 AI 응답을 MessageRecord로 저장**
   - `sender_type='ai'` 설정
   - `sequence=2` (고객 메시지 다음 번호)
   - 저장소에 저장

4. ✅ **ConversationResponse에 AI 메시지 포함**
   - 스키마: `backend/app/schemas/conversation.py`
   - 응답에 고객 메시지 + AI 메시지 함께 반환

5. ✅ **테스트 업데이트**
   - 계약 테스트: `backend/tests/contract/test_conversations.py`
   - 유닛 테스트: `backend/tests/unit/test_conversation_service.py`
   - LLM 모킹 전략 수립

### 가치
- ✅ 즉시 AI 응답 제공 시작
- ✅ MVP 핵심 기능 완성
- ✅ 파일럿 테스트 가능

### 리스크 & 완화
- **리스크**: LLM API 호출 실패
  - **완화**: `fallback_text` 파라미터 활용, 사용자 친화적 오류 메시지
- **리스크**: 응답 지연 (3초 목표)
  - **완화**: 비동기 처리, 프론트엔드 로딩 상태 표시

### 의존성
- 없음 (즉시 시작 가능)

---

## 📋 Task 2: Qdrant 벡터 검색 통합 [P2]

### 목표
지식 베이스를 벡터 임베딩하여 RAG 패턴으로 LLM 응답 품질 향상

### 구현 단계
1. ✅ **Qdrant 클라이언트 설정**
   - 파일: `backend/core/config.py`, `backend/app/services/vector_service.py`
   - Qdrant 연결 설정 (호스트, API 키, 컬렉션명)
   - 클라이언트 초기화 및 헬스체크

2. ✅ **지식 베이스 임베딩 스크립트**
   - 파일: `backend/infrastructure/embeddings/ingest.py`
   - 문서 로딩 (Markdown, PDF, JSON 등)
   - OpenAI Embeddings API 호출
   - Qdrant 업로드 (배치 처리)

3. ✅ **벡터 검색 서비스 구현**
   - 파일: `backend/app/services/vector_service.py`
   - 대화 컨텍스트 기반 쿼리 벡터 생성
   - Qdrant 유사도 검색 (top-k=3~5)
   - 결과 포맷팅 및 반환

4. ✅ **LLM 프롬프트에 컨텍스트 주입**
   - 파일: `backend/app/services/conversation_service.py`
   - 벡터 검색 결과를 시스템 메시지에 추가
   - 컨텍스트 윈도우 크기 관리

5. ✅ **성능 테스트 및 최적화**
   - 파일: `backend/tests/integration/test_vector_service.py`
   - 검색 지연시간 측정 (목표: <100ms)
   - 캐싱 전략 적용

### 가치
- ✅ AI 응답 정확도 및 관련성 대폭 향상
- ✅ 지식 베이스 활용으로 일관된 정보 제공
- ✅ 환각(hallucination) 감소

### 리스크 & 완화
- **리스크**: 임베딩 API 비용 및 지연시간
  - **완화**: 배치 임베딩, 캐싱, 증분 업데이트
- **리스크**: Qdrant 인프라 설정 복잡도
  - **완화**: Managed Qdrant Cloud 사용 고려
- **리스크**: 컨텍스트 윈도우 크기 제한
  - **완화**: 동적 top-k 조정, 컨텍스트 압축

### 의존성
- **Task 1 (LLM 통합)** 완료 필요

### 병렬 실행 가능
- ✅ Task 3 (HITL UI)와 동시 개발 가능

---

## 📋 Task 3: HITL 승인 UI 구현 [P3]

### 목표
에이전트가 AI 응답을 검토하고 승인/수정/거부할 수 있는 인터페이스 제공

### 구현 단계
1. ✅ **승인 대기 큐 API**
   - 파일: `backend/app/api/v1/approvals.py`
   - GET `/v1/approvals/pending` (대기 중인 승인 목록)
   - POST `/v1/approvals/{id}/approve` (승인)
   - POST `/v1/approvals/{id}/reject` (거부)
   - PUT `/v1/approvals/{id}/modify` (수정 후 승인)

2. ✅ **승인 서비스 로직**
   - 파일: `backend/app/services/approval_service.py`
   - 승인 상태 관리 (pending → approved/rejected)
   - 수정된 메시지 저장
   - 타임아웃 처리 (5분 후 자동 에스컬레이션)

3. ✅ **프론트엔드 승인 대기 목록 페이지**
   - 파일: `frontend/src/features/approvals/pages/PendingApprovalsPage.tsx`
   - 대기 큐 목록 표시 (우선순위, 대기시간)
   - 필터링 및 정렬 기능

4. ✅ **승인 검토 UI 컴포넌트**
   - 파일: `frontend/src/features/approvals/components/ApprovalReviewPanel.tsx`
   - 원본 AI 응답 vs 수정 버전 비교 UI
   - 인라인 편집 기능
   - 승인/거부 버튼

5. ✅ **승인 완료 후 고객 전송**
   - 파일: `backend/app/services/conversation_service.py`
   - 승인된 메시지를 대화에 추가
   - 고객에게 응답 전송 (채널 통합 시)

6. ✅ **E2E 테스트**
   - 파일: `frontend/tests/e2e/approval-workflow.spec.ts`
   - 승인/거부/수정 워크플로우 전체 시나리오

### 가치
- ✅ AI 응답 품질 보증
- ✅ 비즈니스 리스크 완화
- ✅ 에이전트 신뢰 확보

### 리스크 & 완화
- **리스크**: 승인 지연 시 고객 대기시간 증가
  - **완화**: 타임아웃 자동 에스컬레이션, 우선순위 큐
- **리스크**: 에이전트 작업 부하 증가
  - **완화**: 자동 승인 임계값 설정 (신뢰도 높은 응답)

### 의존성
- **Task 1 (LLM 통합)** 완료 필요

### 병렬 실행 가능
- ✅ Task 2 (Qdrant)와 동시 개발 가능

---

## 📋 Task 4: Supabase Realtime 연동 [P4]

### 목표
대화 및 승인 상태 변경 시 실시간 동기화로 협업 경험 향상

### 구현 단계
1. ✅ **Realtime 채널 설정**
   - 파일: `frontend/src/services/realtime.ts`
   - Supabase 클라이언트 초기화
   - 채널 구독 로직 (conversations, approvals)

2. ✅ **대화 상태 변경 이벤트 브로드캐스트**
   - 파일: `backend/app/services/conversation_service.py`
   - 메시지 추가, 상태 변경 시 Supabase Broadcast
   - 이벤트 페이로드 설계

3. ✅ **승인 상태 변경 이벤트 브로드캐스트**
   - 파일: `backend/app/services/approval_service.py`
   - 승인/거부/수정 시 이벤트 발행

4. ✅ **프론트엔드 Realtime 구독 훅**
   - 파일: `frontend/src/hooks/useConversationUpdates.ts`
   - 파일: `frontend/src/hooks/useApprovalUpdates.ts`
   - 구독 라이프사이클 관리
   - 이벤트 핸들러 등록

5. ✅ **UI 자동 갱신**
   - 파일: `frontend/src/features/chat/components/ChatPanel.tsx`
   - 파일: `frontend/src/features/approvals/components/QueueStatusList.tsx`
   - Realtime 이벤트 수신 시 상태 업데이트
   - 낙관적 업데이트(Optimistic UI)

6. ✅ **연결 상태 관리**
   - 파일: `frontend/src/services/realtime.ts`
   - 연결 끊김 감지 및 재연결
   - 오프라인 모드 처리

### 가치
- ✅ 실시간 협업 경험
- ✅ 에이전트 생산성 향상
- ✅ 데이터 일관성 보장

### 리스크 & 완화
- **리스크**: Realtime 연결 불안정성
  - **완화**: 재연결 로직, 폴링 폴백
- **리스크**: 이벤트 순서 보장 이슈
  - **완화**: 시퀀스 번호, 타임스탬프 기반 정렬
- **리스크**: 스케일링 시 채널 관리 복잡도
  - **완화**: 채널 네이밍 전략, 권한 관리

### 의존성
- **Task 3 (HITL UI)** 완료 필요

---

## 📋 Task 5: 실시간 대시보드 구현 [P5]

### 목표
감독자용 실시간 메트릭 및 대화 현황 모니터링 UI

### 구현 단계
1. ✅ **메트릭 집계 API**
   - 파일: `backend/app/api/v1/metrics.py`
   - GET `/v1/metrics/conversations` (대화 통계)
   - GET `/v1/metrics/approvals` (승인 현황)
   - GET `/v1/metrics/performance` (성능 지표)

2. ✅ **대화 통계 쿼리**
   - 파일: `backend/app/repositories/metrics_repository.py`
   - 활성/대기/완료 대화 수
   - 평균 응답 시간, 해결 시간
   - 시간대별 트렌드

3. ✅ **승인 현황 통계**
   - 파일: `backend/app/repositories/metrics_repository.py`
   - 대기/승인/거부/자동승인 비율
   - 평균 승인 시간

4. ✅ **대시보드 메트릭 카드 UI**
   - 파일: `frontend/src/features/dashboard/components/MetricCards.tsx`
   - KPI 카드 (활성 대화, 대기 승인, 평균 응답시간)
   - 색상 코딩 (정상/경고/위험)

5. ✅ **실시간 활동 타임라인**
   - 파일: `frontend/src/features/dashboard/components/ActivityTimeline.tsx`
   - 최근 대화 활동 피드
   - 승인 이벤트 로그

6. ✅ **Realtime 메트릭 갱신**
   - 파일: `frontend/src/features/dashboard/pages/DashboardPage.tsx`
   - Realtime 이벤트로 메트릭 자동 업데이트
   - 폴링 폴백 (30초 간격)

7. ✅ **차트 및 시각화**
   - 파일: `frontend/src/features/dashboard/components/ConversationChart.tsx`
   - Recharts 라이브러리
   - 시간대별 대화량 차트
   - 승인 비율 파이 차트

### 가치
- ✅ 운영 가시성
- ✅ 성능 모니터링
- ✅ 데이터 기반 의사결정

### 리스크 & 완화
- **리스크**: 복잡한 쿼리로 인한 성능 저하
  - **완화**: 쿼리 최적화, 캐싱, 인덱싱
- **리스크**: 실시간 업데이트 빈도 최적화
  - **완화**: 디바운싱, 배치 업데이트

### 의존성
- **Task 4 (Realtime 연동)** 완료 필요

---

## 🗺️ 실행 전략 & 타임라인

### Phase 1: 핵심 AI 기능 (Week 1)
**기간**: 2-3일
**작업**: Task 1 - LLM과 대화 API 완전 통합
**마일스톤**: ✅ AI 응답 생성 가능
**배포 가능**: ✅ 파일럿 테스트 시작

### Phase 2: 품질 향상 및 보증 (Week 1-2)
**기간**: 5-6일 (병렬 실행)
**작업**:
- Task 2 - Qdrant 벡터 검색 통합 (병렬)
- Task 3 - HITL 승인 UI 구현 (병렬)

**마일스톤**: ✅ 품질 향상 및 보증 메커니즘 완성
**배포 가능**: ✅ 프로덕션 준비

### Phase 3: 실시간 협업 (Week 2-3)
**기간**: 3-4일
**작업**: Task 4 - Supabase Realtime 연동
**마일스톤**: ✅ 실시간 협업 기능
**배포 가능**: ✅ 멀티 에이전트 환경 지원

### Phase 4: 운영 모니터링 (Week 3)
**기간**: 4-5일
**작업**: Task 5 - 실시간 대시보드
**마일스톤**: ✅ 운영 모니터링 완성
**배포 가능**: ✅ 엔터프라이즈 준비

### 총 예상 기간
- **순차 실행**: 18-23일
- **병렬 실행 (권장)**: 14-18일

---

## 🎯 핵심 성공 요인

1. ✅ **Phase 1 완료 후 즉시 파일럿 테스트**
   - 빠른 피드백 루프
   - 실제 사용 패턴 학습

2. ✅ **Phase 2 병렬 실행으로 시간 단축**
   - Qdrant와 HITL UI는 독립적
   - 5-6일로 압축 가능

3. ✅ **점진적 배포로 리스크 완화**
   - 각 Phase 완료 시 배포
   - 롤백 포인트 확보

4. ✅ **테스트 커버리지 유지**
   - 각 Task별 유닛/통합/E2E 테스트
   - CI/CD 파이프라인 통합

---

## 🚀 다음 즉시 실행 액션

### Task 1 시작: LLM과 대화 API 완전 통합

**Step 1**: ConversationService에 LLMService 의존성 주입
```python
# backend/app/services/conversation_service.py

from .llm_service import LLMService

class ConversationService:
    def __init__(
        self,
        repository: ConversationRepository,
        llm_service: LLMService  # 추가
    ) -> None:
        self._repository = repository
        self._llm_service = llm_service  # 추가
```

**Step 2**: start_conversation에서 AI 응답 생성
```python
async def start_conversation(
    self, payload: StartConversationRequest
) -> ConversationResponse:
    # 기존: 대화 및 고객 메시지 저장
    conversation_record, message_records = await self._persist_entities(payload)

    # 신규: LLM 호출하여 AI 응답 생성
    ai_response = await self._generate_ai_response(
        customer_message=payload.message.body
    )

    # 신규: AI 응답을 MessageRecord로 저장
    ai_message = await self._save_ai_message(
        conversation_id=conversation_record.id,
        content=ai_response.content,
        sequence=2
    )

    # 응답에 AI 메시지 포함
    return ConversationResponse(
        conversation=self._to_conversation_resource(conversation_record),
        messages=[
            self._to_message_resource(message_records[0]),  # 고객 메시지
            self._to_message_resource(ai_message),  # AI 메시지
        ],
        pending_approval=True  # Phase 2에서 HITL 적용 시 사용
    )
```

**예상 완료**: 2-3일
**마일스톤**: AI 응답 자동 생성 동작

---

## 📝 메모리 저장 위치

모든 설계는 `ai-contact-center` 네임스페이스에 저장되었습니다:
- ✅ `ai-contact-center/analysis-session`: 분석 세션 메타데이터
- ✅ `ai-contact-center/current-status`: 현재 구현 상태
- ✅ `ai-contact-center/priority-analysis`: 우선순위 분석 결과
- ✅ `ai-contact-center/task-1-llm-integration`: Task 1 상세 계획
- ✅ `ai-contact-center/task-2-qdrant-integration`: Task 2 상세 계획
- ✅ `ai-contact-center/task-3-hitl-ui`: Task 3 상세 계획
- ✅ `ai-contact-center/task-4-realtime`: Task 4 상세 계획
- ✅ `ai-contact-center/task-5-dashboard`: Task 5 상세 계획
- ✅ `ai-contact-center/dependency-graph`: 의존성 그래프
- ✅ `ai-contact-center/implementation-roadmap`: 구현 로드맵 요약

---

**문서 버전**: 1.0
**최종 업데이트**: 2025-10-30
**작성자**: AI Agent (Claude Code)
