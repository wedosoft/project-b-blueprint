-- Row-level security policies for core chat tables
-- Assumes authenticated users have entries in public.users with matching auth_user_id

CREATE OR REPLACE FUNCTION public.current_user_record()
RETURNS public.users
LANGUAGE sql
SECURITY DEFINER
SET search_path = public
AS $$
  SELECT u
  FROM public.users u
  WHERE u.auth_user_id = auth.uid()
    AND u.status = 'active'
  LIMIT 1;
$$;

CREATE OR REPLACE FUNCTION public.current_user_org_id()
RETURNS uuid
LANGUAGE sql
SECURITY DEFINER
SET search_path = public
AS $$
  SELECT u.organization_id
  FROM public.users u
  WHERE u.auth_user_id = auth.uid()
    AND u.status = 'active'
  LIMIT 1;
$$;

CREATE OR REPLACE FUNCTION public.current_user_role()
RETURNS user_role
LANGUAGE sql
SECURITY DEFINER
SET search_path = public
AS $$
  SELECT u.role
  FROM public.users u
  WHERE u.auth_user_id = auth.uid()
    AND u.status = 'active'
  LIMIT 1;
$$;

GRANT EXECUTE ON FUNCTION public.current_user_record() TO authenticated;
GRANT EXECUTE ON FUNCTION public.current_user_org_id() TO authenticated;
GRANT EXECUTE ON FUNCTION public.current_user_role() TO authenticated;

-- Conversations
ALTER TABLE public.conversations ENABLE ROW LEVEL SECURITY;

CREATE POLICY conversations_service_role_all ON public.conversations
  USING (auth.role() = 'service_role')
  WITH CHECK (auth.role() = 'service_role');

CREATE POLICY conversations_select_org ON public.conversations
  FOR SELECT
  USING (
    auth.role() = 'service_role'
    OR (
      EXISTS (
        SELECT 1
        FROM public.users u
        WHERE u.auth_user_id = auth.uid()
          AND u.status = 'active'
          AND (
            u.organization_id = conversations.organization_id
            OR u.id = conversations.customer_user_id
          )
      )
    )
  );

CREATE POLICY conversations_insert_agents ON public.conversations
  FOR INSERT
  WITH CHECK (
    auth.role() = 'service_role'
    OR (
      EXISTS (
        SELECT 1
        FROM public.users u
        WHERE u.auth_user_id = auth.uid()
          AND u.status = 'active'
          AND u.organization_id = conversations.organization_id
          AND u.role IN ('agent', 'supervisor')
      )
    )
  );

CREATE POLICY conversations_update_agents ON public.conversations
  FOR UPDATE
  USING (
    auth.role() = 'service_role'
    OR (
      EXISTS (
        SELECT 1
        FROM public.users u
        WHERE u.auth_user_id = auth.uid()
          AND u.status = 'active'
          AND u.organization_id = conversations.organization_id
          AND u.role IN ('agent', 'supervisor')
      )
    )
  )
  WITH CHECK (
    auth.role() = 'service_role'
    OR (
      EXISTS (
        SELECT 1
        FROM public.users u
        WHERE u.auth_user_id = auth.uid()
          AND u.status = 'active'
          AND u.organization_id = conversations.organization_id
          AND u.role IN ('agent', 'supervisor')
      )
    )
  );

-- Messages
ALTER TABLE public.messages ENABLE ROW LEVEL SECURITY;

CREATE POLICY messages_service_role_all ON public.messages
  USING (auth.role() = 'service_role')
  WITH CHECK (auth.role() = 'service_role');

CREATE POLICY messages_select_conversation ON public.messages
  FOR SELECT
  USING (
    auth.role() = 'service_role'
    OR (
      EXISTS (
        SELECT 1
        FROM public.users u
        JOIN public.conversations c ON c.id = public.messages.conversation_id
        WHERE u.auth_user_id = auth.uid()
          AND u.status = 'active'
          AND (
            u.organization_id = c.organization_id
            OR u.id = c.customer_user_id
          )
      )
    )
  );

CREATE POLICY messages_insert_participants ON public.messages
  FOR INSERT
  WITH CHECK (
    auth.role() = 'service_role'
    OR (
      EXISTS (
        SELECT 1
        FROM public.users u
        JOIN public.conversations c ON c.id = public.messages.conversation_id
        WHERE u.auth_user_id = auth.uid()
          AND u.status = 'active'
          AND (
            (
              u.role = 'customer'
              AND u.id = c.customer_user_id
            )
            OR (
              u.role IN ('agent', 'supervisor')
              AND u.organization_id = c.organization_id
            )
          )
      )
    )
  );

-- AI responses
ALTER TABLE public.ai_responses ENABLE ROW LEVEL SECURITY;

CREATE POLICY ai_responses_service_role_all ON public.ai_responses
  USING (auth.role() = 'service_role')
  WITH CHECK (auth.role() = 'service_role');

CREATE POLICY ai_responses_select_org ON public.ai_responses
  FOR SELECT
  USING (
    auth.role() = 'service_role'
    OR (
      EXISTS (
        SELECT 1
        FROM public.users u
        JOIN public.conversations c ON c.id = public.ai_responses.conversation_id
        WHERE u.auth_user_id = auth.uid()
          AND u.status = 'active'
          AND (
            u.organization_id = c.organization_id
            OR u.id = c.customer_user_id
          )
      )
    )
  );

CREATE POLICY ai_responses_update_agents ON public.ai_responses
  FOR UPDATE
  USING (
    auth.role() = 'service_role'
    OR (
      EXISTS (
        SELECT 1
        FROM public.users u
        JOIN public.conversations c ON c.id = public.ai_responses.conversation_id
        WHERE u.auth_user_id = auth.uid()
          AND u.status = 'active'
          AND u.organization_id = c.organization_id
          AND u.role IN ('agent', 'supervisor')
      )
    )
  )
  WITH CHECK (
    auth.role() = 'service_role'
    OR (
      EXISTS (
        SELECT 1
        FROM public.users u
        JOIN public.conversations c ON c.id = public.ai_responses.conversation_id
        WHERE u.auth_user_id = auth.uid()
          AND u.status = 'active'
          AND u.organization_id = c.organization_id
          AND u.role IN ('agent', 'supervisor')
      )
    )
  );

-- Approval records
ALTER TABLE public.approval_records ENABLE ROW LEVEL SECURITY;

CREATE POLICY approval_records_service_role_all ON public.approval_records
  USING (auth.role() = 'service_role')
  WITH CHECK (auth.role() = 'service_role');

CREATE POLICY approval_records_select_org ON public.approval_records
  FOR SELECT
  USING (
    auth.role() = 'service_role'
    OR (
      EXISTS (
        SELECT 1
        FROM public.users u
        JOIN public.ai_responses r ON r.id = public.approval_records.ai_response_id
        JOIN public.conversations c ON c.id = r.conversation_id
        WHERE u.auth_user_id = auth.uid()
          AND u.status = 'active'
          AND u.organization_id = c.organization_id
      )
    )
  );

CREATE POLICY approval_records_insert_agents ON public.approval_records
  FOR INSERT
  WITH CHECK (
    auth.role() = 'service_role'
    OR (
      EXISTS (
        SELECT 1
        FROM public.users u
        JOIN public.ai_responses r ON r.id = public.approval_records.ai_response_id
        JOIN public.conversations c ON c.id = r.conversation_id
        WHERE u.auth_user_id = auth.uid()
          AND u.status = 'active'
          AND u.organization_id = c.organization_id
          AND u.role IN ('agent', 'supervisor')
      )
    )
  );
