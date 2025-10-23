---
description: "Task list for AI Contact Center OS MVP feature implementation"
---

# Tasks: AI Contact Center OS MVP

**Input**: Design documents from `/specs/001-ai-contact-center-mvp/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

## Format: `[ID] [P?] [Story] Description`
- **[P]**: Task can run in parallel (different files, no blocking dependencies)
- **[Story]**: User story label from spec.md (US1–US5)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Establish governance and scaffold the dual-project workspace

- [x] T001 Commit ratified principles and gate criteria to `.specify/memory/constitution.md`
- [x] T002 Create backend directory skeleton per plan (e.g., `backend/app/api`, `backend/app/services`, `backend/tests`)
- [x] T003 [P] Initialize backend project dependencies in `backend/pyproject.toml` with FastAPI, Pydantic v2, httpx, supabase-py, qdrant-client, APScheduler
- [x] T004 [P] Scaffold React/Vite workspace with Chakra UI, tanstack-query, supabase-js, Zustand in `frontend/`
- [x] T005 Define environment contract documenting required secrets in `.env.example`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before any user story work begins

- [x] T006 Configure Supabase project linkage and CLI settings in `supabase/config.toml`
- [x] T007 Generate initial Postgres migration from data model in `supabase/migrations/20251022_initial_schema.sql`
- [x] T008 [P] Author row-level security policies for conversations/messages/approvals in `supabase/policies/mvp_policies.sql`
- [x] T009 [P] Implement centralized settings loader covering Supabase, Qdrant, LLM, Fly.io in `backend/app/core/config.py`
- [x] T010 [P] Create Qdrant bootstrap and health-check script in `backend/infrastructure/embeddings/bootstrap_qdrant.py`
- [x] T011 Implement LLM orchestration wrapper with retry & fallback in `backend/app/services/llm_service.py`
- [x] T012 Implement background scheduler bootstrap with APScheduler in `backend/app/workers/scheduler.py`
- [x] T013 Define Supabase Realtime channel contracts and payload schema in `supabase/realtime/conversation_channels.sql`
- [x] T014 Configure CI/CD pipeline deploying to Fly.io and running pytest/pnpm tests in `.github/workflows/mvp-ci.yml`

**Checkpoint**: Foundational infrastructure ready — proceed to user stories

---

## Phase 3: User Story 1 – Customer Receives AI-Powered Responses (Priority: P1) 🎯 MVP

**Goal**: 고객이 텍스트 채널에서 질문하면 3초 이내 AI 응답을 받고, 필요 시 HITL 검토 큐로 자동 전환되도록 한다.

**Independent Test**: 다양한 고객 질문을 전송했을 때 응답이 생성되고, 임계값 이하 신뢰도는 대기열로 이동하며, 승인 후 고객이 자연스럽게 응답을 수신하는지 확인한다.

### Tests (write first)

- [x] T015 [P] [US1] 작성된 계약대로 POST `/conversations`를 검증하는 Schemathesis 테스트 추가 in `backend/tests/contract/test_conversations.py`
- [x] T016 [P] [US1] 채팅 컴포저 및 응답 렌더링 유닛 테스트 작성 in `frontend/tests/unit/chatComposer.test.tsx`

### Implementation

- [ ] T017 [P] [US1] 대화/메시지 Pydantic 스키마 정의 in `backend/app/schemas/conversation.py`
- [ ] T018 [P] [US1] 대화 및 메시지 영속 로직 구현 in `backend/app/repositories/conversation_repository.py`
- [ ] T019 [US1] 벡터 검색+LLM 파이프라인 조립하는 서비스 구현 in `backend/app/services/conversation_service.py`
- [ ] T020 [US1] 고객 대화 생성 및 메시지 추가 API 라우트 구현 in `backend/app/api/routes/conversations.py`
- [ ] T021 [US1] Qdrant 검색 어댑터와 임베딩 캐시 작성 in `backend/infrastructure/embeddings/qdrant_client.py`
- [ ] T022 [US1] 고객 채팅 UI 및 스트리밍 응답 처리 구현 in `frontend/src/features/chat/components/ChatPanel.tsx`
- [ ] T023 [US1] Realtime 브로드캐스트 퍼블리셔 모듈 작성 in `backend/app/services/realtime_publisher.py`
- [ ] T024 [US1] 벡터 미스·LLM 오류 대비 fallback 처리와 텔레메트리 추가 in `backend/app/services/conversation_service.py`

**Checkpoint**: 고객 채팅 흐름이 독립적으로 동작하며 승인 큐 연동 준비됨

---

## Phase 4: User Story 2 – Agent Reviews and Approves AI Responses (Priority: P1)

**Goal**: 상담사가 대기열에서 AI 응답을 검토/승인/수정/거부하고, 승인 결과가 즉시 고객에게 전달되도록 한다.

**Independent Test**: 신뢰도 임계값 이하 응답을 생성 후 상담사 계정으로 로그인해 승인, 수정, 거부 흐름이 실시간으로 반영되는지 확인한다.

### Tests (write first)

- [ ] T025 [P] [US2] GET `/approvals/pending` 응답 형식을 검증하는 계약 테스트 작성 in `backend/tests/contract/test_approvals.py`
- [ ] T026 [P] [US2] 승인/수정/거부 통합 시나리오 테스트 작성 in `backend/tests/integration/test_approvals.py`

### Implementation

- [ ] T027 [P] [US2] 승인 큐 조회용 저장소 작성 in `backend/app/repositories/approval_repository.py`
- [ ] T028 [US2] 승인 결정 비즈니스 로직 구현 in `backend/app/services/approval_service.py`
- [ ] T029 [US2] 승인 대기 목록 API 라우트 구현 in `backend/app/api/routes/approvals.py`
- [ ] T030 [US2] 승인/수정/거부 결정 API 엔드포인트 구현 in `backend/app/api/routes/approvals.py`
- [ ] T031 [US2] 승인 타임아웃 처리 APScheduler 잡 등록 in `backend/app/workers/scheduler.py`
- [ ] T032 [US2] 상담사 승인 대시보드 페이지 구현 in `frontend/src/features/approvals/pages/PendingApprovalsPage.tsx`
- [ ] T033 [US2] Supabase Realtime 구독 훅 구현으로 큐 갱신 in `frontend/src/features/approvals/hooks/useApprovalChannel.ts`

**Checkpoint**: HITL 승인 프로세스가 독립적으로 검증 가능

---

## Phase 5: User Story 3 – Supervisor Monitors Performance via Dashboard (Priority: P2)

**Goal**: 감독자가 실시간으로 핵심 KPI를 조회하고, 기간/에이전트/토픽 필터링이 가능한 대시보드를 제공한다.

**Independent Test**: 대화와 승인 이벤트를 발생시키고 대시보드 카드와 차트가 2초 이내 갱신되며 필터가 정확히 반영되는지 확인한다.

### Tests (write first)

- [ ] T034 [P] [US3] GET `/dashboard/summary` 계약 테스트 작성 in `backend/tests/contract/test_dashboard.py`
- [ ] T035 [P] [US3] 메트릭 집계 통합 테스트 작성 in `backend/tests/integration/test_dashboard_metrics.py`

### Implementation

- [ ] T036 [P] [US3] 메트릭 조회용 저장소 구현 in `backend/app/repositories/metric_repository.py`
- [ ] T037 [US3] 대시보드 서비스와 캐시 전략 구현 in `backend/app/services/dashboard_service.py`
- [ ] T038 [US3] 대시보드 요약/시계열 API 라우트 구현 in `backend/app/api/routes/dashboard.py`
- [ ] T039 [US3] 메트릭 스냅샷 뷰 또는 함수 정의 in `supabase/functions/dashboard_metrics.sql`
- [ ] T040 [US3] 대시보드 페이지 및 필터 상태 관리 구현 in `frontend/src/features/dashboard/pages/DashboardPage.tsx`
- [ ] T041 [US3] KPI 카드 및 차트 컴포넌트 구성 in `frontend/src/features/dashboard/components/MetricCards.tsx`

**Checkpoint**: 대시보드 스토리가 독립적으로 검증 가능

---

## Phase 6: User Story 4 – User Authentication and Access Control (Priority: P2)

**Goal**: 고객/상담사/감독자 역할 기반 인증·인가를 구현하고 세션 만료 및 접근 제한을 강제한다.

**Independent Test**: 각 역할로 로그인하여 허용된 화면만 접근 가능한지, 1시간 미활동 시 자동 로그아웃이 수행되는지 확인한다.

### Implementation

- [ ] T042 [P] [US4] 역할별 접근 제어 통합 테스트 작성 in `backend/tests/integration/test_auth_roles.py`
- [ ] T043 [US4] Supabase auth 및 RLS 정책 정의 in `supabase/policies/auth_roles.sql`
- [ ] T044 [US4] 백엔드 인증 미들웨어/의존성 구현 in `backend/app/api/dependencies/auth.py`
- [ ] T045 [US4] 세션 타임아웃 및 재인증 로직 구현 in `backend/app/services/session_service.py`
- [ ] T046 [US4] 프론트엔드 역할 가드 컴포넌트 구현 in `frontend/src/app/guards/RequireRole.tsx`
- [ ] T047 [US4] 감독자 사용자 관리 UI 구현 in `frontend/src/features/admin/pages/UserManagementPage.tsx`

**Checkpoint**: 역할 기반 접근 제어 독립 검증 완료

---

## Phase 7: User Story 5 – Real-time Conversation Status Tracking (Priority: P3)

**Goal**: 고객·상담사 모두가 대화 상태(자동응답, 대기, 인간 상담 전환 등)를 실시간으로 확인하도록 한다.

**Independent Test**: 여러 대화 상태 전환을 시뮬레이션하여 고객/상담사 화면에서 상태와 타이핑 표시가 즉시 갱신되는지 검증한다.

### Implementation

- [ ] T048 [P] [US5] 실시간 상태 전파 통합 테스트 작성 in `backend/tests/integration/test_realtime_status.py`
- [ ] T049 [US5] 대화 상태 브로드캐스터 서비스 구현 in `backend/app/services/status_stream.py`
- [ ] T050 [US5] 상태 채널 payload 스키마 정의 in `supabase/realtime/conversation_status.sql`
- [ ] T051 [US5] 고객용 상태 인디케이터 컴포넌트 구현 in `frontend/src/features/chat/components/ConversationStatusIndicator.tsx`
- [ ] T052 [US5] 상담사용 상태 대시보드 컴포넌트 구현 in `frontend/src/features/approvals/components/QueueStatusList.tsx`

**Checkpoint**: 상태 추적 스토리가 독립적으로 검증 가능

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: 문서화, 성능, 보안 등 전반적 품질 개선

- [ ] T053 [P] 작성된 운영 절차를 `docs/runbooks/mvp.md`에 정리
- [ ] T054 부하 시험 스크립트 추가 in `backend/tests/performance/load_test.py`
- [ ] T055 보안 통제 및 비상 대응 플랜 문서화 in `docs/security/controls.md`
- [ ] T056 Quickstart 절차 검증 체크리스트 작성 in `docs/checklists/quickstart-validation.md`

---

## Dependencies & Execution Order

### Phase Dependencies
- **Phase 1 → Phase 2** → 모든 사용자 스토리 이전에 완료해야 함
- **User Stories (Phases 3–7)**: Foundational 완료 후 우선순위(P1→P2→P3)에 따라 순차 진행 권장, 팀 여건 시 병렬 가능
- **Phase 8**: 모든 구현 완료 후 수행

### User Story Dependencies
- **US1**: Foundational 이후 즉시 착수 가능, 다른 스토리의 선행 조건
- **US2**: US1 출력(대기열 이벤트)이 있어야 완전 검증 가능하나 구현 자체는 Foundational 후 시작 가능
- **US3**: 메트릭 데이터는 US1/US2 이벤트를 참조하지만 API/프론트는 독립 구성 가능
- **US4**: 인증 체계는 US1~US3 UI 보호를 위해 조기 통합 권장
- **US5**: US1/US2 상태 전이 이벤트를 구독하므로 해당 이벤트 퍼블리시가 준비되어야 시험 가능

### Parallel Opportunities
- Setup 단계에서 T003–T005는 서로 다른 경로라 병렬 처리 가능
- Foundational 단계의 T008–T014 중 서로 다른 파일을 다루는 작업은 병렬 수행 가능
- 각 사용자 스토리 내 [P] 태스크는 테스트, 저장소, UI 등 충돌 없는 파일을 다루므로 병렬화 가능
- 서로 다른 사용자 스토리는 팀원이 분업 시 병렬 진행 가능하되, Realtime 이벤트 정의(T013, T023, T033, T050)는 공유 의존성을 주의

---

## Implementation Strategy

### MVP 우선 (US1 중심)
1. Phases 1–2 완료 후 US1을 집중 구현
2. US1 검증 및 데모 → 초기 고객 피드백 수집

### 점진적 확장
1. US2로 HITL 승인 기능 추가
2. US3 대시보드, US4 인증, US5 실시간 상태 기능 순으로 증분 배포

### 병렬 팀 전략
- 백엔드/프론트엔드 담당을 나누고, 공통 인프라(T006–T014)를 먼저 확정한 뒤 각 스토리 팀이 독립적으로 진행
- 정기적으로 계약 테스트와 Realtime 스키마를 공유해 인터페이스 드리프트를 방지
