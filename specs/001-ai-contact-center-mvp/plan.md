# Implementation Plan: AI Contact Center OS MVP

**Branch**: `001-ai-contact-center-mvp` | **Date**: 2025-10-22 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-ai-contact-center-mvp/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

텍스트 기반 고객 상담 흐름에 AI 응답을 적용하고 HITL 검토와 실시간 대시보드로 품질을 보증하는 MVP를 구축한다. FastAPI+Supabase 백엔드가 세션·권한·대화 로그를 관리하고 Qdrant 벡터 검색과 OpenAI/Claude LLM을 조합한다. React+Chakra UI 프론트엔드는 고객 채팅, 에이전트 승인, 감독자 대시보드를 제공하며 Supabase Realtime으로 상태를 동기화한다.

## Technical Context

<!--
  ACTION REQUIRED: Replace the content in this section with the technical details
  for the project. The structure here is presented in advisory capacity to guide
  the iteration process.
-->

**Language/Version**: Backend Python 3.11 (FastAPI), Frontend TypeScript 5.x + React 18 (Vite build), Infrastructure automation via Bash/Terraform (TBD)  
**Primary Dependencies**: FastAPI, Pydantic v2, httpx, supabase-py, qdrant-client, OpenAI Python SDK, APScheduler, Supabase Realtime; React 18, Chakra UI, tanstack-query, supabase-js, Zustand  
**Storage**: Supabase PostgreSQL (auth, conversations, approvals), Qdrant managed collection (embeddings), Supabase object storage for transcripts & attachments (Phase 1+)  
**Testing**: Backend pytest + httpx.AsyncClient + respx; contract tests with schemathesis (Phase 1); Frontend Vitest + React Testing Library; Playwright E2E (Phase 2 gate)  
**Target Platform**: Containerized Linux backend (Supabase-hosted Postgres/Qdrant) deployed to Fly.io; SPA frontend targeting evergreen browsers (Chrome/Edge/Firefox) with Supabase-hosted static delivery
**Project Type**: Full-stack web application with separated backend (`backend/`) and frontend (`frontend/`) workspaces  
**Performance Goals**: Initial AI response ≤3s (p95); vector search latency ≤100ms for ≥80% queries; dashboard refresh latency ≤2s; sustain 100 concurrent conversations in load test  
**Constraints**: Chat channel only for MVP; HITL auto-escalation after 5 minutes; session timeout 1 hour; conversation retention 1 year; graceful LLM failure messaging (generic customer notice + detailed agent alert)  
**Scale/Scope**: Pilot with ≤3 고객사 또는 10 internal agents; ≤500 conversations/day; ≤10 concurrent agents; ≤50k knowledge items embedded

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- Gate (NEEDS CLARIFICATION): `.specify/memory/constitution.md` is still a template with no ratified principles. Populate or formally waive the constitution before Phase 1 sign-off.
- Interim practice: operate under global instructions (Korean-only comms, no hardcoding, explicit failure handling) and re-evaluate once the constitution is authored.

## Project Structure

### Documentation (this feature)

```
specs/001-ai-contact-center-mvp/
├── spec.md                # Feature specification (complete)
├── plan.md                # Implementation plan (this file)
├── checklists/
│   └── requirements.md    # Validation checklist (complete)
├── research.md            # Phase 0 research summary (TBD)
├── data-model.md          # Phase 1 data modeling deliverable (TBD)
├── quickstart.md          # Phase 1 onboarding guide (TBD)
└── contracts/             # Phase 1 API/schema contracts (TBD)
```

### Source Code (repository root)
<!--
  ACTION REQUIRED: Replace the placeholder tree below with the concrete layout
  for this feature. Delete unused options and expand the chosen structure with
  real paths (e.g., apps/admin, packages/something). The delivered plan must
  not include Option labels.
-->

```
backend/
├── app/
│   ├── api/
│   ├── services/
│   ├── repositories/
│   ├── schemas/
│   └── workers/
├── core/
│   ├── config/
│   └── logging/
├── infrastructure/
│   └── embeddings/        # Embedding jobs & ingestion scripts
├── scripts/
└── tests/
    ├── unit/
    ├── integration/
    └── contract/

frontend/
├── src/
│   ├── components/
│   ├── pages/
│   ├── features/
│   ├── hooks/
│   └── services/
├── public/
└── tests/
    ├── unit/
    ├── integration/
    └── e2e/

shared/
└── packages/              # Shared TypeScript/Python utilities (Phase 1+)
```

**Structure Decision**: Adopt a dual-package web application. `backend/` delivers FastAPI APIs, workers, and contract tests; `frontend/` serves the React client for chat, approvals, and dashboards; `shared/` houses future cross-cutting utilities once reuse is proven.

## Complexity Tracking

*Fill ONLY if Constitution Check has violations that must be justified*

현재 헌법 위반 없음.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |
## Phase 0 Research Scope

- Deployment platform → Fly.io (research.md)
- LLM provider → OpenAI GPT-4 Turbo (research.md)
- Real-time channel → Supabase Realtime (research.md)
- Background jobs → FastAPI BackgroundTasks + APScheduler (research.md)
- Constitution path → Draft minimal principles before Phase 1 (research.md)
- Infrastructure automation → CLI-first (Supabase/Fly) with Terraform deferred (research.md)

