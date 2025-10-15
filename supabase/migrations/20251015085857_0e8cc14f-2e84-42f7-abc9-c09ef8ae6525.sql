-- sessions 테이블을 티켓 시스템으로 확장
ALTER TABLE sessions ADD COLUMN IF NOT EXISTS status text DEFAULT 'pending';
ALTER TABLE sessions ADD COLUMN IF NOT EXISTS title text;
ALTER TABLE sessions ADD COLUMN IF NOT EXISTS updated_at timestamp with time zone DEFAULT now();

-- 상태 유효성 검사 (트리거 사용)
CREATE OR REPLACE FUNCTION check_session_status()
RETURNS TRIGGER AS $$
BEGIN
  IF NEW.status NOT IN ('pending', 'in_progress', 'resolved', 'closed') THEN
    RAISE EXCEPTION 'Invalid status value';
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER validate_session_status
BEFORE INSERT OR UPDATE ON sessions
FOR EACH ROW
EXECUTE FUNCTION check_session_status();

-- updated_at 자동 업데이트 트리거
CREATE OR REPLACE FUNCTION update_sessions_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_sessions_updated_at 
BEFORE UPDATE ON sessions
FOR EACH ROW 
EXECUTE FUNCTION update_sessions_updated_at();