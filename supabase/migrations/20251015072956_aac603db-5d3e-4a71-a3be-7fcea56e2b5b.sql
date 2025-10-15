-- AI 컨택센터 세션 및 메시지 테이블
CREATE TABLE public.sessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
  agent_id TEXT NOT NULL,
  customer_name TEXT,
  customer_id TEXT
);

-- 대화 메시지 테이블
CREATE TABLE public.messages (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id UUID REFERENCES public.sessions(id) ON DELETE CASCADE NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
  speaker TEXT NOT NULL CHECK (speaker IN ('agent', 'customer')),
  text TEXT NOT NULL,
  masked_text TEXT
);

-- AI 제안 결과 테이블
CREATE TABLE public.ai_suggestions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id UUID REFERENCES public.sessions(id) ON DELETE CASCADE NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
  type TEXT NOT NULL CHECK (type IN ('summary', 'emotion', 'intent', 'reply')),
  text TEXT NOT NULL,
  score DECIMAL,
  context_refs JSONB,
  metadata JSONB
);

-- 피드백 테이블
CREATE TABLE public.feedback (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  suggestion_id UUID REFERENCES public.ai_suggestions(id) ON DELETE CASCADE NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
  approved BOOLEAN NOT NULL,
  reason TEXT
);

-- 감사 로그 테이블
CREATE TABLE public.audit_log (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
  event TEXT NOT NULL,
  input_hash TEXT,
  model_id TEXT,
  latency INTEGER,
  dlp_flag BOOLEAN DEFAULT false
);

-- RLS 정책 활성화
ALTER TABLE public.sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.ai_suggestions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.feedback ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.audit_log ENABLE ROW LEVEL SECURITY;

-- 모든 사용자가 자신의 데이터에 접근 가능 (MVP에서는 간단하게 설정)
CREATE POLICY "Public access for sessions" ON public.sessions FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Public access for messages" ON public.messages FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Public access for ai_suggestions" ON public.ai_suggestions FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Public access for feedback" ON public.feedback FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Public access for audit_log" ON public.audit_log FOR ALL USING (true) WITH CHECK (true);

-- 실시간 업데이트 활성화
ALTER TABLE public.messages REPLICA IDENTITY FULL;
ALTER PUBLICATION supabase_realtime ADD TABLE public.messages;

ALTER TABLE public.ai_suggestions REPLICA IDENTITY FULL;
ALTER PUBLICATION supabase_realtime ADD TABLE public.ai_suggestions;