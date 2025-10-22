-- Supabase Realtime channel contracts for AI Contact Center OS MVP
-- Define broadcast channels and row-level publication configuration.

-- Conversations channel: publishes status transitions and pending approvals.
-- Payload schema (JSON):
-- {
--   "event": "conversation_status_changed",
--   "conversation_id": "<uuid>",
--   "organization_id": "<uuid>",
--   "status": "<enum:conversation_status>",
--   "previous_status": "<enum:conversation_status|null>",
--   "pending_approval_response_id": "<uuid|null>",
--   "updated_at": "<timestamptz>",
--   "metadata": {
--     "reason": "<enum:conversation_status_reason>",
--     "confidence": "<numeric|null>"
--   }
-- }
-- Triggered on insert/update of conversations and conversation_status_history.

-- Approvals channel: publishes HITL queue updates.
-- Payload schema (JSON):
-- {
--   "event": "approval_queue_updated",
--   "conversation_id": "<uuid>",
--   "ai_response_id": "<uuid>",
--   "organization_id": "<uuid>",
--  "confidence": "<numeric>",
--   "requires_approval": "<boolean>",
--   "status": "<enum:ai_response_status>",
--   "submitted_at": "<timestamptz>",
--   "priority": "<enum:conversation_priority>",
--   "context": {
--     "customer_question": "<text>",
--     "proposed_answer": "<text>"
--   }
-- }
-- Triggered on insert/update of ai_responses and approval_records.

-- Metrics channel (future phase): publishes dashboard aggregates.
-- Payload schema (JSON):
-- {
--   "event": "metrics_snapshot",
--   "organization_id": "<uuid>",
--   "collected_at": "<timestamptz>",
--   "metric": "<enum:dashboard_metric>",
--   "value": "<numeric>",
--   "breakdown": "<jsonb>"
-- }

-- Enable logical replication on relevant tables.
ALTER PUBLICATION supabase_realtime ADD TABLE public.conversations;
ALTER PUBLICATION supabase_realtime ADD TABLE public.conversation_status_history;
ALTER PUBLICATION supabase_realtime ADD TABLE public.ai_responses;
ALTER PUBLICATION supabase_realtime ADD TABLE public.approval_records;

-- Ensure triggers for broadcast events (requires Supabase edge functions or serverless hooks).
-- The actual trigger functions are implemented in backend services; this file documents the contract.
