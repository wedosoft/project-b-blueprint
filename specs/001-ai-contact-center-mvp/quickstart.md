# Quickstart – AI Contact Center OS MVP

## 목적
새로운 팀원이 AI Contact Center OS MVP 환경을 수 시간 내에 준비하고, 핵심 유저 스토리(P1) 흐름을 셀프 테스트할 수 있도록 안내한다.

## 사전 준비물
- macOS / Linux 개발 환경 (Windows 사용 시 WSL2 권장)
- Python 3.11 (추천: `pyenv` 또는 `uv`), `pipx`
- Node.js 20.x 및 `pnpm` 9.x
- Supabase CLI (`brew install supabase/tap/supabase`)
- Fly.io CLI (`brew install flyctl`)
- Qdrant Cloud 프로젝트 (API Key, URL)
- OpenAI API Key (GPT-4 Turbo) 및 optional Claude Key (fallback)
- GitHub Personal Access Token (GitHub Actions 연동 시)

## 1. 레포지토리 클론
```bash
git clone git@github.com:wedosoft/project-b-blueprint.git
cd project-b-blueprint
```
브랜치 `001-ai-contact-center-mvp`를 체크아웃한다.

## 2. 환경 변수 구성
`cp .env.example .env` (존재 시) 또는 아래 키를 `.env`에 수동 추가한다.
```
# Supabase
SUPABASE_URL=...
SUPABASE_SERVICE_ROLE_KEY=...
SUPABASE_ANON_KEY=...

# Database
DATABASE_URL=postgresql://postgres:[password]@[host]:6543/postgres

# Qdrant
QDRANT_URL=...
QDRANT_API_KEY=...
QDRANT_COLLECTION=ccos-mvp

# LLM
OPENAI_API_KEY=...
OPENAI_MODEL=gpt-4.1-mini
ANTHROPIC_API_KEY=...           # optional fallback

# Fly.io
FLY_API_TOKEN=...

# Observability
SENTRY_DSN=...                   # optional
```
> **주의**: 각 키는 1Password 또는 Vault에서 발급한다. 로컬 `.env`는 Git에 커밋하지 않는다.

## 3. Supabase 프로젝트 연결
```bash
supabase login
supabase link --project-ref <PROJECT_REF>
```
- `supabase/config.toml`이 생성되며, 데이터베이스 마이그레이션과 시드 작업을 동일한 CLI에서 수행한다.
- 로컬 개발 시 `supabase start`로 Postgres + Studio + Edge Runtime을 띄울 수 있다.

## 4. 데이터베이스 및 Qdrant 준비
1. 스키마 적용
   ```bash
   supabase db push
   ```
2. 초기 시드 (테넌트, 샘플 상담사 계정, 더미 지식 항목)
   ```bash
   supabase db seed --file supabase/seed/mvp.sql
   ```
3. Qdrant 컬렉션 생성 (한 번만 수행)
   ```bash
   python -m venv .venv && source .venv/bin/activate
   pip install qdrant-client python-dotenv
   python scripts/bootstrap_qdrant.py
   ```

## 5. 백엔드(FastAPI) 환경
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
alembic upgrade head           # Supabase db push 대신 자체 마이그레이션 사용 시
uvicorn app.main:app --reload
```
- `app/core/config.py`가 `.env`를 로드하도록 확인한다.
- APScheduler 스케줄러는 앱 시작 시 등록되어 승인 타임아웃을 주기적으로 점검한다.

## 6. 프론트엔드(React) 환경
```bash
cd ../frontend
pnpm install
pnpm dev
```
- `.env.local`에 Supabase 클라이언트 키와 Fly.io API 엔드포인트를 설정한다.
- `pnpm test`로 유닛 테스트, `pnpm lint`로 린트를 실행한다.

## 7. GitHub Actions & Fly.io 배포 예행
1. Fly.io 앱 생성
   ```bash
   flyctl launch --no-deploy --copy-config
   ```
2. GitHub Actions 시크릿 등록
   ```bash
   gh secret set FLY_API_TOKEN --body "$FLY_API_TOKEN"
   gh secret set SUPABASE_SERVICE_ROLE_KEY --body "$SUPABASE_SERVICE_ROLE_KEY"
   ```
3. 배포 파이프라인 테스트
   ```bash
   flyctl deploy --remote-only
   ```

## 8. P1 유저 스토리 검증 루프
1. **US1 (고객 AI 응답)**
   - 프론트엔드 `http://localhost:5173` 접속 → 고객 채널에서 질문 전송
   - 실시간 응답이 3초 이내 도착하는지 확인 (`Network` 탭에서 `response_latency_ms` 확인)
2. **US2 (HITL 승인)**
   - 상담사 계정으로 로그인 → `Pending Approvals` 큐 확인
   - 승인/수정/거부 작업 후 고객 화면에서 결과가 즉시 적용되는지 확인
3. **US3 (대시보드)**
   - Supervisor 로그인 → KPI 카드와 차트가 2초 이내 갱신되는지 확인
   - 시간 범위 및 에이전트 필터 변경 후 데이터가 정확히 필터링되는지 검사
4. **실패 시나리오**
   - OpenAI API Key를 임시로 잘못 설정 → 고객에게는 일반 오류, 상담사에게는 상세 알림이 노출되는지 확인
   - Qdrant에서 빈 결과가 날 때 수동 승인 플로우로 전환되는지 확인

## 9. 테스트 실행
- 백엔드 유닛/통합: `cd backend && pytest`
- 계약 테스트(Phase 2 준비): `pytest -m contract` 또는 `schemathesis run specs/001-ai-contact-center-mvp/contracts/openapi.yaml`
- 프론트엔드 유닛: `cd frontend && pnpm test`
- E2E(작성 후): `pnpm exec playwright test`

## 10. 트러블슈팅 포인트
- Supabase Row-Level Security가 활성화되면 정책을 추가해야 고객/상담사가 자신이 속한 조직 데이터만 조회 가능
- Fly.io 배포 시 장시간 실행되는 WebSocket을 지원하려면 `[[services.concurrency]]` 설정을 `soft_limit=25`, `hard_limit=50`으로 조정
- APScheduler가 중복 실행되지 않도록 Fly.io에서는 1 인스턴스만 스케줄러 태스크를 수행하도록 `leader election` 플래그 사용 (예: Redis Lock 또는 Fly Machines with PRIMARY)
- Realtime 이벤트 누락 시 `supabase-js` 버전을 최신으로 유지하고 `presence` 기능 대신 `broadcast` 채널 사용을 권장
