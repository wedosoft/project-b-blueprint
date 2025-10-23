# AI Contact Center OS Constitution

## Core Principles

### I. Human-Assured AI Quality
Every customer-facing response must either exceed the 80 percent confidence threshold or pass a human-in-the-loop review. The transition between automated and human-reviewed replies stays auditable and recoverable at all times.

### II. Test-First Contracts
API surfaces, data models, and realtime channels are specified with schemas and contract tests before implementation. Each user story ships with at least one independently runnable test that fails prior to development.

### III. Operational Resilience
Failures in LLM, Supabase, Qdrant, or downstream services trigger safe fallbacks for customers and actionable alerts for agents. Deployments verify the 3s response, 100ms search, and 2s dashboard latency targets before and after release.

### IV. Least-Privilege Access
Customer, agent, and supervisor roles are isolated through Supabase Auth and row-level security. Approval and dashboard flows remain gated behind authentication, sessions expire after one hour of inactivity, and privilege changes take effect immediately.

### V. Continuous Observability & Feedback
Conversations, approvals, errors, and SLA metrics are emitted via structured logs and dashboards. Feedback loops run on a two-week cadence, and experimental changes are recorded with measurable KPIs.

## Guardrails

- Stack: Backend uses FastAPI, Pydantic v2, APScheduler, httpx, supabase-py, and qdrant-client. Frontend uses React 18, Chakra UI, tanstack-query, supabase-js, and Zustand. OpenAI GPT-4 Turbo is the default LLM, with Claude as contingency per plan.md.
- Deployment: Backend runs on Fly.io containers; Supabase manages Postgres, Auth, and Realtime; Qdrant is managed. Infrastructure-as-code moves to Terraform after MVP, but current automation must rely on `.specify/scripts` and CLI workflows.
- Performance & Reliability: Maintain 3s p95 initial AI responses, 100ms vector searches for 80 percent of queries, 2s dashboard refresh, and 100 simultaneous conversations. On failure, send generic customer fallback messages and detailed agent alerts.
- Data Retention: Persist conversation logs for one year, enforce Supabase security policies for sensitive data, and version vector embeddings when schema changes.

## Workflow & Quality Gates

- Keep Phase 1 artefacts (plan, spec, research, data-model, contracts, quickstart, tasks) under `/specs/001-ai-contact-center-mvp/` and update linked tests or TODOs with every change.
- Follow the ordered gates: Phase 1 Setup → Foundational → User Stories (US1 → US5) → Polish. Do not start a downstream phase until the prior gate is complete.
- All implementation pull requests must show failing pre-written tests, land code that turns them green, and run Schemathesis, pytest, and pnpm test scripts before merge.
- Realtime updates must be reviewed jointly by backend and frontend owners, ensuring Supabase channel definitions and client hooks stay in lockstep.

## Governance

- This constitution governs all MVP development decisions. Exceptions require documentation in `plan.md`, explicit mitigations, team lead approval, and an updated `Last Amended` date.
- Reviewers must confirm every pull request adheres to the principles, guardrails, and workflow gates, or record an approved deviation with remediation steps.
- Amendments demand updates to supporting research/plan files, a new semantic version, and refreshed ratification metadata in this document.

**Version**: 1.0.1 | **Ratified**: 2025-10-22 | **Last Amended**: 2025-10-23
