# AI Contact Center MVP

Next-generation AI-powered contact center with Human-in-the-Loop (HITL) approval workflow.

## 🎯 MVP Features

### ✅ Implemented

- **US1: Customer receives AI-powered responses**
  - Real-time chat interface
  - AI response generation with confidence scoring
  - Knowledge base integration via Qdrant vector search
  - 80% confidence threshold for HITL approval

- **US2: Agent reviews and approves AI responses**
  - Real-time approval queue
  - Approve/Modify/Reject workflow
  - Priority-based ordering
  - Turnaround time tracking

- **US3: Supervisor monitors performance**
  - Dashboard with key metrics
  - System health monitoring
  - (MVP: Mock data, real-time coming soon)

## 🏗️ Architecture

```
Frontend (React + TypeScript + Chakra UI)
    ↓ REST API
Backend (FastAPI + Python)
    ↓
├─ Supabase (PostgreSQL)
├─ Qdrant (Vector DB)
└─ OpenAI (LLM)
```

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- pnpm 9+
- Supabase account
- Qdrant Cloud account
- OpenAI API key

### Backend Setup

1. **Environment Configuration**

```bash
cd backend
cp .env.example .env
```

Edit `.env` with your credentials:

```env
OPENAI_API_KEY=sk-...
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJ...
SUPABASE_ANON_KEY=eyJ...
QDRANT_URL=https://xxx.qdrant.io
QDRANT_API_KEY=xxx
BACKEND_BASE_URL=http://localhost:8000
FRONTEND_ORIGIN=http://localhost:5173
```

2. **Install Dependencies**

```bash
pip install -e ".[dev]"
```

3. **Run Database Migrations**

```bash
# Apply schema to Supabase
psql $SUPABASE_DATABASE_URL < supabase/migrations/20251022_initial_schema.sql
```

4. **Start Backend Server**

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API will be available at http://localhost:8000

- Swagger docs: http://localhost:8000/docs
- Health check: http://localhost:8000/health

### Frontend Setup

1. **Environment Configuration**

```bash
cd frontend
cp .env.example .env
```

Edit `.env`:

```env
VITE_BACKEND_URL=http://localhost:8000
VITE_SUPABASE_URL=https://xxx.supabase.co
VITE_SUPABASE_ANON_KEY=eyJ...
```

2. **Install Dependencies**

```bash
pnpm install
```

3. **Start Development Server**

```bash
pnpm dev
```

Frontend will be available at http://localhost:5173

## 📡 API Endpoints

### Conversations

- `POST /v1/conversations` - Start new conversation with AI response
- `GET /v1/conversations/{id}` - Retrieve conversation details

### Approvals

- `GET /v1/approvals/pending?organization_id={id}` - List pending approvals
- `POST /v1/approvals/{ai_response_id}/approve` - Process approval action

## 🗄️ Database Schema

Key tables:
- `conversations` - Conversation metadata and status
- `messages` - Customer/AI/Agent messages
- `ai_responses` - LLM outputs with confidence scores
- `approval_records` - HITL review audit trail
- `knowledge_items` - Knowledge base content
- `knowledge_embedding_jobs` - Vector embedding tracking

See `supabase/migrations/20251022_initial_schema.sql` for full schema.

## 🧪 Testing

### Backend Tests

```bash
cd backend
pytest tests/
```

### Frontend Tests

```bash
cd frontend
pnpm test
```

## 🚢 Deployment

### Backend (Fly.io)

```bash
cd backend
fly deploy
```

### Frontend (Vercel)

```bash
cd frontend
vercel deploy --prod
```

## 🔧 Configuration

### Confidence Threshold

Default: 80% (0.80)

Adjust in `backend/app/services/ai_response_service.py`:

```python
CONFIDENCE_THRESHOLD = 0.80  # Change as needed
```

### LLM Settings

Configure in `.env`:

```env
LLM_PROVIDER=openai
OPENAI_MODEL=gpt-4-turbo
LLM_FALLBACK_MODEL=gpt-3.5-turbo
LLM_TIMEOUT_SECONDS=30
```

## 📊 Monitoring

- **Health Check**: `GET /health`
- **Logs**: Check Fly.io logs or local stdout
- **Database**: Supabase dashboard
- **Vector DB**: Qdrant console

## 🛣️ Roadmap

### Phase 2 (Coming Soon)
- Real-time dashboard metrics
- WebSocket/Supabase Realtime integration
- Multi-message conversations
- Agent takeover flow

### Phase 3
- Voice channel support (STT/TTS)
- Email integration
- Multi-agent workflows

### Phase 4+
- Knowledge graph integration
- RLHF training pipeline
- Advanced analytics

## 📝 License

Proprietary - AI Contact Center Team

## 🤝 Contributing

1. Create feature branch from `main`
2. Implement changes with tests
3. Submit PR with clear description
4. Ensure CI passes

## 📞 Support

For issues or questions, please check:
- [Specification](specs/001-ai-contact-center-mvp/spec.md)
- [Development Guide](AGENTS.md)
- GitHub Issues
