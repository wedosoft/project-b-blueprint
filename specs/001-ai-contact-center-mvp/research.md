# Phase 0 Research – AI Contact Center OS MVP

## Overview
- 목적: MVP 구현 전에 핵심 기술 선택과 미정 항목을 확정해 Phase 1 설계·구현 리스크를 줄인다.
- 범위: 배포 대상, LLM 공급자, 실시간 통신 채널, 백그라운드 작업 처리, 헌법(프로젝트 원칙) 준비, 인프라 자동화 전략.

## Decision Log

### Deployment Platform – Fly.io
- **Task**: "Research deployment platform (Fly.io vs Supabase Edge vs others) for FastAPI backend"
- **Decision**: FastAPI 백엔드를 Fly.io에 컨테이너로 배포한다.
- **Rationale**:
  - FastAPI 컨테이너 배포 사례가 풍부하고, 무료 플랜으로 초기 실험 가능.
  - Supabase(PostgreSQL/Qdrant)는 매니지드 서비스로 유지하며, Fly.io와의 네트워크 구성이 단순.
  - GitHub Actions → Fly.io 배포 파이프라인 구성이 간단하고 롤백 지원.
- **Alternatives considered**:
  - Supabase Edge Functions: 초단기 요청 지향 → 장기 실행 API에 부적합.
  - Vercel/Netlify: 장기 SSE·WebSocket 제약으로 채팅 MVP에 부적합.
- **Follow-up**: Phase 1에서 Dockerfile과 Fly.io 배포 설정 정의.

### LLM Provider – OpenAI GPT-4 Turbo
- **Task**: "Research primary LLM provider for Korean text support and latency"
- **Decision**: OpenAI GPT-4 Turbo(필요 시 GPT-4o mini) 조합을 기본으로 사용한다.
- **Rationale**:
  - 한국어 대응 품질과 API 안정성이 검증되어 있음.
  - 함수 호출, 응답 스트리밍, 토큰 단가 측면에서 예측 가능성이 높음.
  - SDK 생태계(파이썬/자바스크립트)와 문서가 풍부해 MVP 속도 확보.
- **Alternatives considered**:
  - Anthropic Claude 3.5: 품질은 좋으나 리전 제약과 비용 변동 폭이 크다.
  - 오픈소스 LLM 자호스팅: 인프라·운영 부담이 커서 MVP 범위 초과.
- **Follow-up**: Phase 1에서 모델 파라미터(temperature, top_p) 기본값과 안전 가드레일 정의.

### Real-time Channel – Supabase Realtime
- **Task**: "Find best practices for real-time messaging in Supabase-backed chat MVP"
- **Decision**: Supabase Realtime(브로드캐스트 + Row-level 리스닝)을 상담 상태, HITL 승인, 대시보드 갱신에 사용한다.
- **Rationale**:
  - 이미 Supabase Auth/DB를 사용하므로 권한 연동이 자연스럽고 운영 복잡도 없음.
  - Row-Level Security와 결합해 상담별 접근 제어 가능.
  - 별도 외부 서비스 도입 대비 비용/구성 요소 최소화.
- **Alternatives considered**:
  - Pusher/Ably: 기능은 풍부하지만 비용/운영 오버헤드 증가.
  - 자체 WebSocket 서버: Sticky 세션 등 운영 부담이 큼.
- **Follow-up**: Phase 1에서 채널 네임스페이스와 이벤트 페이로드 스키마 설계.

### Background Work Processing – FastAPI BackgroundTasks + APScheduler
- **Task**: "Research background job handling for embedding generation & HITL timeouts"
- **Decision**: FastAPI BackgroundTasks로 단발 작업을 처리하고, APScheduler로 주기적 검사를 진행한다.
- **Rationale**:
  - 예상 부하(≤500 대화/일, 동시 상담 ≤10)에서는 단일 프로세스 기반 비동기 처리로 충분.
  - 추가 인프라(Celery/Redis 등) 없이도 MVP 기간에 필요한 기능을 구현 가능.
  - Failover 시 Fly.io 인스턴스 확장으로 대응 가능.
- **Alternatives considered**:
  - Celery+Redis: 확장성은 높지만 초기 설정/운영이 무겁다.
  - Supabase Functions/Edge Workers: 장기 실행 및 상태 관리 제한.
- **Follow-up**: Phase 1에서 APScheduler 작업 등록과 실패 시 알림 경로 정의.

### Constitution Path – Minimal Principles before Phase 1
- **Task**: "Define interim project constitution based on global rules"
- **Decision**: Phase 1 착수 전까지 최소 원칙(테스트 전략, 코드 리뷰 기준, 배포 게이트 등)을 `.specify/memory/constitution.md`에 작성한다.
- **Rationale**:
  - 현재 템플릿 상태라 품질 게이트를 enforce 할 수 없음.
  - 글로벌 지침(한국어 커뮤니케이션, 하드코딩 금지, 실패 시 명시적 오류 등)을 헌법에 반영해 일관성 확보.
- **Alternatives considered**:
  - 헌법 미작성: `/speckit.plan` 흐름에서 Gate 통과 불가.
- **Follow-up**: Phase 1 kick-off 시 책임자 지정 및 초안 일정 수립.

### Infrastructure Automation – CLI-first, Terraform Deferred
- **Task**: "Evaluate need for Terraform/IaC during MVP"
- **Decision**: Supabase CLI와 Fly.io CLI를 사용한 스크립트 기반 배포를 우선 적용하고, Terraform 도입은 PoC 이후로 미룬다.
- **Rationale**:
  - 현재 리소스 수가 제한적이므로 CLI+GitHub Actions 조합으로도 충분히 재현 가능.
  - Terraform 도입은 스테이트 관리, 접근 제어 등 준비 비용이 높음.
  - MVP 단계에서는 빠른 반복과 실험이 우선.
- **Alternatives considered**:
  - Terraform 즉시 도입: 장점은 있으나 초기 설정과 권한 관리가 무거움.
  - 완전 수동 배포: 이력 추적이 어렵고 오류 위험이 높음.
- **Follow-up**: Phase 1에서 GitHub Actions 워크플로에 Fly/Supabase CLI 통합 스크립트 작성.

## Outstanding Actions
- [ ] 헌법 초안 책임자 및 완료 목표일 정의 (Phase 1 시작 전)
