-- AI Contact Center OS MVP initial schema
BEGIN;

CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "citext";

-- Enumerations
CREATE TYPE organization_status AS ENUM ('active', 'suspended');
CREATE TYPE user_role AS ENUM ('customer', 'agent', 'supervisor');
CREATE TYPE user_status AS ENUM ('active', 'inactive');
CREATE TYPE conversation_channel AS ENUM ('text-web');
CREATE TYPE conversation_status AS ENUM (
  'active',
  'pending_approval',
  'awaiting_agent',
  'agent_live',
  'escalated',
  'resolved',
  'closed',
  'error'
);
CREATE TYPE conversation_priority AS ENUM ('standard', 'high', 'vip');
CREATE TYPE conversation_status_reason AS ENUM (
  'confidence_threshold',
  'agent_decision',
  'timeout',
  'system_error',
  'manual_override'
);
CREATE TYPE message_sender_type AS ENUM ('customer', 'ai', 'agent', 'system');
CREATE TYPE llm_provider AS ENUM ('openai', 'anthropic', 'fallback');
CREATE TYPE ai_response_status AS ENUM ('pending', 'approved', 'modified', 'rejected', 'superseded', 'failed');
CREATE TYPE approval_action AS ENUM ('approved', 'modified', 'rejected', 'auto_escalated', 'timeout');
CREATE TYPE embedding_job_status AS ENUM ('pending', 'processing', 'succeeded', 'failed');
CREATE TYPE dashboard_metric AS ENUM (
  'active_conversations',
  'avg_confidence',
  'approval_rate',
  'response_p95_ms',
  'escalations',
  'customer_csats'
);

-- Organizations
CREATE TABLE public.organizations (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name text NOT NULL,
  slug text UNIQUE,
  timezone text NOT NULL DEFAULT 'Asia/Seoul',
  status organization_status NOT NULL DEFAULT 'active',
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX organizations_status_idx ON public.organizations (status);

-- Users
CREATE TABLE public.users (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  auth_user_id uuid NOT NULL UNIQUE,
  organization_id uuid NOT NULL REFERENCES public.organizations (id) ON DELETE CASCADE,
  role user_role NOT NULL,
  email citext NOT NULL UNIQUE,
  full_name text NOT NULL,
  display_name text,
  status user_status NOT NULL DEFAULT 'active',
  last_login_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX users_role_idx ON public.users (role);
CREATE INDEX users_organization_role_idx ON public.users (organization_id, role);

-- Conversations
CREATE TABLE public.conversations (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id uuid NOT NULL REFERENCES public.organizations (id) ON DELETE CASCADE,
  customer_user_id uuid REFERENCES public.users (id) ON DELETE SET NULL,
  external_customer_ref text,
  channel conversation_channel NOT NULL DEFAULT 'text-web',
  status conversation_status NOT NULL DEFAULT 'active',
  priority conversation_priority NOT NULL DEFAULT 'standard',
  started_at timestamptz NOT NULL DEFAULT now(),
  ended_at timestamptz,
  last_activity_at timestamptz NOT NULL DEFAULT now(),
  pending_approval_response_id uuid,
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX conversations_org_status_idx ON public.conversations (organization_id, status);
CREATE INDEX conversations_last_activity_idx ON public.conversations (last_activity_at DESC);
CREATE INDEX conversations_pending_approval_idx ON public.conversations (pending_approval_response_id)
  WHERE pending_approval_response_id IS NOT NULL;

-- Conversation status history
CREATE TABLE public.conversation_status_history (
  id bigserial PRIMARY KEY,
  conversation_id uuid NOT NULL REFERENCES public.conversations (id) ON DELETE CASCADE,
  previous_status conversation_status NOT NULL,
  new_status conversation_status NOT NULL,
  reason conversation_status_reason NOT NULL,
  actor_user_id uuid REFERENCES public.users (id) ON DELETE SET NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX conversation_status_history_conversation_id_created_at_idx
  ON public.conversation_status_history (conversation_id, created_at DESC);

-- Messages
CREATE TABLE public.messages (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  conversation_id uuid NOT NULL REFERENCES public.conversations (id) ON DELETE CASCADE,
  sender_type message_sender_type NOT NULL,
  sender_user_id uuid REFERENCES public.users (id) ON DELETE SET NULL,
  body text NOT NULL,
  attachments jsonb NOT NULL DEFAULT '[]'::jsonb,
  ai_response_id uuid,
  sequence integer NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX messages_conversation_sequence_idx ON public.messages (conversation_id, sequence);

-- AI responses
CREATE TABLE public.ai_responses (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  conversation_id uuid NOT NULL REFERENCES public.conversations (id) ON DELETE CASCADE,
  message_id uuid NOT NULL REFERENCES public.messages (id) ON DELETE CASCADE,
  llm_provider llm_provider NOT NULL,
  llm_model text NOT NULL,
  confidence numeric(5, 4) NOT NULL,
  requires_approval boolean NOT NULL,
  status ai_response_status NOT NULL DEFAULT 'pending',
  knowledge_sources jsonb NOT NULL DEFAULT '[]'::jsonb,
  prompt_tokens integer NOT NULL,
  completion_tokens integer NOT NULL,
  latency_ms integer NOT NULL,
  error_reason text,
  generated_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX ai_responses_conversation_status_idx ON public.ai_responses (conversation_id, status);
CREATE INDEX ai_responses_requires_approval_idx ON public.ai_responses (requires_approval)
  WHERE requires_approval;

-- Approval records
CREATE TABLE public.approval_records (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  ai_response_id uuid NOT NULL UNIQUE REFERENCES public.ai_responses (id) ON DELETE CASCADE,
  agent_id uuid NOT NULL REFERENCES public.users (id),
  action approval_action NOT NULL,
  submitted_text text NOT NULL,
  notes text,
  turnaround_ms integer NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX approval_records_agent_action_idx ON public.approval_records (agent_id, action);

-- Knowledge items
CREATE TABLE public.knowledge_items (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id uuid NOT NULL REFERENCES public.organizations (id) ON DELETE CASCADE,
  title text NOT NULL,
  content text NOT NULL,
  source_uri text,
  tags text[] NOT NULL DEFAULT '{}'::text[],
  last_reviewed_at timestamptz,
  version integer NOT NULL DEFAULT 1,
  is_active boolean NOT NULL DEFAULT true,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX knowledge_items_org_active_idx ON public.knowledge_items (organization_id, is_active);
CREATE INDEX knowledge_items_tags_gin ON public.knowledge_items USING GIN (tags);

-- Knowledge embedding jobs
CREATE TABLE public.knowledge_embedding_jobs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  knowledge_item_id uuid NOT NULL REFERENCES public.knowledge_items (id) ON DELETE CASCADE,
  qdrant_point_id text UNIQUE,
  status embedding_job_status NOT NULL,
  error_message text,
  embedding_model text NOT NULL,
  vector_dimension integer NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

-- Metric snapshots
CREATE TABLE public.metric_snapshots (
  id bigserial PRIMARY KEY,
  organization_id uuid NOT NULL REFERENCES public.organizations (id) ON DELETE CASCADE,
  collected_at timestamptz NOT NULL,
  "window" interval NOT NULL,
  metric dashboard_metric NOT NULL,
  value numeric NOT NULL,
  breakdown jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX metric_snapshots_org_metric_time_idx
  ON public.metric_snapshots (organization_id, metric, collected_at);
CREATE INDEX metric_snapshots_metric_window_idx
  ON public.metric_snapshots (metric, "window");

-- Cross-table constraints created after dependent tables exist
ALTER TABLE public.messages
  ADD CONSTRAINT messages_ai_response_id_fkey
  FOREIGN KEY (ai_response_id) REFERENCES public.ai_responses (id) ON DELETE SET NULL;
CREATE UNIQUE INDEX messages_ai_response_id_key
  ON public.messages (ai_response_id) WHERE ai_response_id IS NOT NULL;

ALTER TABLE public.conversations
  ADD CONSTRAINT conversations_pending_approval_response_id_fkey
  FOREIGN KEY (pending_approval_response_id) REFERENCES public.ai_responses (id) ON DELETE SET NULL;

COMMIT;
