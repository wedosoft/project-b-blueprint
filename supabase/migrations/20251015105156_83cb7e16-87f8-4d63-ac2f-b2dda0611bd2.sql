-- 보안 이슈 수정: search_path 설정
CREATE OR REPLACE FUNCTION check_session_status()
RETURNS TRIGGER 
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
  IF NEW.status NOT IN ('pending', 'in_progress', 'resolved', 'closed') THEN
    RAISE EXCEPTION 'Invalid status value';
  END IF;
  RETURN NEW;
END;
$$;

CREATE OR REPLACE FUNCTION update_sessions_updated_at()
RETURNS TRIGGER 
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$;