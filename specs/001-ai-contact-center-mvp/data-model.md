# Data Model – AI Contact Center OS MVP

## Domain Scope
- 다중 고객사(Organization) 환경에서 텍스트 기반 상담을 관리하고, AI 응답과 HITL 승인 이력을 일관되게 기록한다.
- 실시간 상담 상태, 대시보드 메트릭, 1년 보존 요건과 감사 추적(approvals, escalations)을 만족한다.
- Supabase PostgreSQL을 권한/트랜잭션 저장소로, Qdrant는 임베딩 벡터 저장소로 사용한다.

## Entity Catalog

### Organization
| Field | Type | Constraints | Description | Source |
| --- | --- | --- | --- | --- |
| id | UUID | PK | 조직 식별자 (다중 고객사 지원) | FR-014 |
| name | text | NOT NULL | 조직명 (고객사 또는 내부 팀) | FR-014 |
| slug | text | UNIQUE | 조직 식별용 슬러그, URL 및 필터링에 사용 | Ops |
| timezone | text | NOT NULL, default 'Asia/Seoul' | 대시보드 집계 기준 시간대 | SC-007 |
| status | enum('active','suspended') | NOT NULL | 조직 활성화 여부 | Ops |
| created_at | timestamptz | NOT NULL, default now() | 생성 시각 | Audit |
| updated_at | timestamptz | NOT NULL, default now() | 마지막 수정 시각 | Audit |

**Indexes**
- `organizations_slug_key`
- `organizations_status_idx`

### User
| Field | Type | Constraints | Description | Source |
| --- | --- | --- | --- | --- |
| id | UUID | PK | 내부 사용자 식별자 | FR-013 |
| auth_user_id | UUID | UNIQUE, NOT NULL | Supabase Auth user id (외부 인증 저장) | FR-013 |
| organization_id | UUID | FK → organizations.id | 소속 조직 | FR-014 |
| role | enum('customer','agent','supervisor') | NOT NULL | 역할 기반 접근 제어 | FR-014, FR-015 |
| email | citext | UNIQUE, NOT NULL | 로그인 및 알림 이메일 | FR-013 |
| full_name | text | NOT NULL | 실명 또는 표시명 | UX |
| display_name | text | NULL | UI 표시용 별칭 | UX |
| status | enum('active','inactive') | NOT NULL | 계정 상태 | FR-013 |
| last_login_at | timestamptz | NULL | 마지막 로그인 | SC-009 |
| created_at | timestamptz | NOT NULL | 생성 시각 | Audit |
| updated_at | timestamptz | NOT NULL | 수정 시각 | Audit |

**Indexes**
- `users_auth_user_id_key`
- `users_role_idx`
- `users_organization_role_idx`

### Conversation
| Field | Type | Constraints | Description | Source |
| --- | --- | --- | --- | --- |
| id | UUID | PK | 대화 식별자 | FR-001 |
| organization_id | UUID | FK → organizations.id | 조직 구분 | FR-032 |
| customer_user_id | UUID | FK → users.id, NULL | 로그인 고객 연결 (비로그인 시 NULL) | FR-001 |
| external_customer_ref | text | NULL | CRM/웹채팅 식별자 | Ops |
| channel | enum('text-web') | NOT NULL | 현재는 텍스트 채널만 지원 | Scope |
| status | enum('active','pending_approval','awaiting_agent','agent_live','escalated','resolved','closed','error') | NOT NULL | 현재 대화 상태 | FR-021 |
| priority | enum('standard','high','vip') | NOT NULL, default 'standard' | 승인 큐 정렬에 사용 | FR-010 |
| started_at | timestamptz | NOT NULL | 대화 시작 시각 | Audit |
| ended_at | timestamptz | NULL | 종료 시각 | FR-032 |
| last_activity_at | timestamptz | NOT NULL | 마지막 메시지 시각 | FR-024 |
| pending_approval_response_id | UUID | FK → ai_responses.id, NULL | 승인 대기 중인 응답 참조 | FR-005 |
| metadata | jsonb | NOT NULL, default '{}' | 세션 정보(브라우저, 진입 경로 등) | FR-025 |
| created_at | timestamptz | NOT NULL | 생성 시각 | Audit |
| updated_at | timestamptz | NOT NULL | 수정 시각 | Audit |

**Indexes**
- `conversations_org_status_idx` (organization_id, status)
- `conversations_last_activity_idx`
- `conversations_pending_approval_idx`

### ConversationStatusHistory
| Field | Type | Constraints | Description | Source |
| --- | --- | --- | --- | --- |
| id | bigserial | PK | 상태 변경 이벤트 id | Audit |
| conversation_id | UUID | FK → conversations.id | 대상 대화 | FR-021 |
| previous_status | text | NOT NULL | 변경 전 상태 | Audit |
| new_status | text | NOT NULL | 변경 후 상태 | FR-021 |
| reason | enum('confidence_threshold','agent_decision','timeout','system_error','manual_override') | NOT NULL | 상태 변경 사유 | Edge |
| actor_user_id | UUID | FK → users.id, NULL | 변경을 일으킨 사용자 | Audit |
| created_at | timestamptz | NOT NULL, default now() | 변경 시각 | Audit |

**Indexes**
- `conversation_status_history_conversation_id_created_at_idx`

### Message
| Field | Type | Constraints | Description | Source |
| --- | --- | --- | --- | --- |
| id | UUID | PK | 메시지 식별자 | FR-001 |
| conversation_id | UUID | FK → conversations.id | 소속 대화 | FR-025 |
| sender_type | enum('customer','ai','agent','system') | NOT NULL | 발신 주체 | FR-024 |
| sender_user_id | UUID | FK → users.id, NULL | agent/system 메시지인 경우 | FR-023 |
| body | text | NOT NULL | 메시지 본문 (Plain text, Markdown 허용) | FR-001 |
| attachments | jsonb | NOT NULL, default '[]' | 추후 파일/링크 확장 대비 | Scope |
| ai_response_id | UUID | FK → ai_responses.id, NULL | AI 메시지인 경우 연결 | FR-002 |
| sequence | integer | NOT NULL | 대화 내 순번 | Edge |
| created_at | timestamptz | NOT NULL | 발신 시각 | Audit |

**Indexes**
- `messages_conversation_sequence_idx`
- `messages_ai_response_id_key`

### AIResponse
| Field | Type | Constraints | Description | Source |
| --- | --- | --- | --- | --- |
| id | UUID | PK | AI 응답 식별자 | FR-002 |
| conversation_id | UUID | FK → conversations.id | 대화 참조 (조인 최적화) | FR-003 |
| message_id | UUID | FK → messages.id | 연결된 메시지 | FR-002 |
| llm_provider | enum('openai','anthropic','fallback') | NOT NULL | 사용된 모델 공급자 | Research |
| llm_model | text | NOT NULL | 모델 이름 (gpt-4.1-mini 등) | FR-002 |
| confidence | numeric(5,4) | NOT NULL | 0~1 신뢰도 점수 | FR-004 |
| requires_approval | boolean | NOT NULL | 승인 필요 여부 (confidence<0.8) | FR-005 |
| status | enum('pending','approved','modified','rejected','superseded','failed') | NOT NULL | 승인 진행 상태 | FR-006 |
| knowledge_sources | jsonb | NOT NULL | 벡터 검색 결과 id/점수 목록 | FR-003 |
| prompt_tokens | integer | NOT NULL | 프롬프트 토큰 수 | Ops |
| completion_tokens | integer | NOT NULL | 응답 토큰 수 | Ops |
| latency_ms | integer | NOT NULL | LLM 응답 시간 | SC-001 |
| error_reason | text | NULL | 실패 시 사유 | FR-027 |
| generated_at | timestamptz | NOT NULL | 생성 시각 | Audit |
| updated_at | timestamptz | NOT NULL | 상태 변경 시각 | Audit |

**Indexes**
- `ai_responses_conversation_status_idx`
- `ai_responses_requires_approval_idx`

### ApprovalRecord
| Field | Type | Constraints | Description | Source |
| --- | --- | --- | --- | --- |
| id | UUID | PK | 승인 행위 식별자 | FR-006 |
| ai_response_id | UUID | FK → ai_responses.id | 대상 AI 응답 | FR-006 |
| agent_id | UUID | FK → users.id | 승인/수정/거부한 상담사 | FR-006 |
| action | enum('approved','modified','rejected','auto_escalated','timeout') | NOT NULL | 수행된 조치 | FR-006, Edge |
| submitted_text | text | NOT NULL | 고객에게 전달된 최종 텍스트 | FR-008 |
| notes | text | NULL | 내부 메모 | FR-012 |
| turnaround_ms | integer | NOT NULL | 승인 요청 → 처리까지 시간 | SC-005 |
| created_at | timestamptz | NOT NULL | 기록 생성 시각 | Audit |

**Indexes**
- `approval_records_agent_action_idx`
- `approval_records_ai_response_id_key`

### KnowledgeItem
| Field | Type | Constraints | Description | Source |
| --- | --- | --- | --- | --- |
| id | UUID | PK | 지식 항목 id | FR-028 |
| organization_id | UUID | FK → organizations.id | 소유 조직 | FR-028 |
| title | text | NOT NULL | 항목 제목 | FR-028 |
| content | text | NOT NULL | 본문 | FR-028 |
| source_uri | text | NULL | 원본 링크 | FR-028 |
| tags | text[] | NOT NULL, default '{}' | 범주 필터링 | Dashboard |
| last_reviewed_at | timestamptz | NULL | 내용 검토 시각 | Ops |
| version | integer | NOT NULL, default 1 | 변경 추적 | Ops |
| is_active | boolean | NOT NULL, default true | 검색 포함 여부 | Ops |
| created_at | timestamptz | NOT NULL | 생성 시각 | Audit |
| updated_at | timestamptz | NOT NULL | 수정 시각 | Audit |

**Indexes**
- `knowledge_items_org_active_idx`
- `knowledge_items_tags_gin`

### KnowledgeEmbeddingJob
| Field | Type | Constraints | Description | Source |
| --- | --- | --- | --- | --- |
| id | UUID | PK | 작업 식별자 | FR-028 |
| knowledge_item_id | UUID | FK → knowledge_items.id | 대상 지식 항목 | FR-028 |
| qdrant_point_id | text | UNIQUE | Qdrant point id | FR-028 |
| status | enum('pending','processing','succeeded','failed') | NOT NULL | 진행 상태 | Ops |
| error_message | text | NULL | 실패 시 에러 메시지 | FR-027 |
| embedding_model | text | NOT NULL | 사용 모델 이름 | Research |
| vector_dimension | integer | NOT NULL | 벡터 차원수 | Research |
| created_at | timestamptz | NOT NULL | 작업 생성 | Audit |
| updated_at | timestamptz | NOT NULL | 상태 변경 | Audit |

### MetricSnapshot
| Field | Type | Constraints | Description | Source |
| --- | --- | --- | --- | --- |
| id | bigserial | PK | 스냅샷 id | FR-016 |
| organization_id | UUID | FK → organizations.id | 조직 | FR-033 |
| collected_at | timestamptz | NOT NULL | 수집 시각 | SC-007 |
| window | interval | NOT NULL | 집계 기간 (예: '5 minutes') | SC-007 |
| metric | enum('active_conversations','avg_confidence','approval_rate','response_p95_ms','escalations','customer_csats') | NOT NULL | 메트릭 종류 | FR-016 |
| value | numeric | NOT NULL | 측정값 | SC-007 |
| breakdown | jsonb | NOT NULL, default '{}' | 필터(에이전트, 토픽, 기간)별 세부값 | FR-033 |
| created_at | timestamptz | NOT NULL | 기록 생성 | Audit |

**Indexes**
- `metric_snapshots_org_metric_time_idx`
- `metric_snapshots_metric_window_idx`

## Relationships
| Parent | Child | Cardinality | Notes |
| --- | --- | --- | --- |
| organizations | users | 1:N | 조직 당 다수 사용자 | FR-014 |
| organizations | conversations | 1:N | 조직 단위 대화 분리 | FR-032 |
| organizations | knowledge_items | 1:N | 지식 베이스 멀티 테넌시 | FR-028 |
| users | conversations | 1:N (nullable) | 로그인 고객이 있는 경우 연결 | FR-001 |
| conversations | messages | 1:N | 메시지 타임라인 | FR-025 |
| messages | ai_responses | 1:1 (optional) | 메시지가 AI 응답인 경우 | FR-002 |
| ai_responses | approval_records | 1:1 | 승인 이력 (최신 기록만 유지) | FR-006 |
| conversations | conversation_status_history | 1:N | 상태 변경 감사 로그 | FR-021 |
| knowledge_items | knowledge_embedding_jobs | 1:N | 재임베딩 가능한 구조 | FR-028 |
| organizations | metric_snapshots | 1:N | 조직별 메트릭 | FR-016 |

## State Machines

### Conversation.status
`active → pending_approval → awaiting_agent → agent_live → resolved → closed`
- `active → pending_approval`: AI 응답 생성 후 confidence < 0.8 (FR-005)
- `pending_approval → awaiting_agent`: 승인 타임아웃 발생, 수동 응답 대기 (Edge case)
- `pending_approval → resolved`: 상담사가 승인/수정 후 즉시 고객에게 전달 (FR-011)
- `any → escalated`: 시스템 오류/AI 실패 시 즉시 인간 상담으로 전환 (FR-027)

### AIResponse.status
`pending → approved|modified|rejected|failed|superseded`
- `pending → approved`: 상담사가 승인 (FR-007)
- `pending → modified`: 상담사가 텍스트 수정 후 전달 (FR-008)
- `pending → rejected`: 상담사가 거부 및 수동 대응 (FR-009)
- `pending → failed`: LLM 에러 또는 벡터 검색 실패 (FR-026, FR-027)
- `approved|modified → superseded`: 후속 응답이 같은 메시지를 대체 (Edge case)

## Data Retention & Compliance
- `conversations`, `messages`, `ai_responses`, `approval_records`: 1년 보존 후 보관 정책에 따라 익명화 또는 삭제 (FR-032).
- `metric_snapshots`: 18개월 롤링 윈도우 유지, 오래된 데이터는 요약본으로 축약.
- `knowledge_items` 버전 관리로 변경 이력 보관, 비활성화 시 검색 제외.

## Operational Notes
- 실시간 상태 및 승인 큐는 Supabase Realtime 채널(`realtime:conversations`, `realtime:approvals`)에서 `conversation_id`, `status`, `pending_approval_response_id`를 브로드캐스트한다.
- 장시간 승인 대기 시 APScheduler가 `approval_records` 없이 `AIResponse.status = 'pending'`인 항목을 스캔하여 `action='timeout'` 레코드를 생성하고 `Conversation.status`를 `awaiting_agent`로 변경한다 (Edge case 대응).
- 벡터 검색 미스 시 `AIResponse.error_reason`과 함께 `ConversationStatusHistory`에 `reason='system_error'` 이벤트를 남겨 추후 튜닝 데이터로 활용 (FR-026).

## Open Questions / Follow-ups
- Supervisor 별 커스텀 메트릭 정의가 필요한 경우 `metric_snapshots`에 JSON Schema 추가 필요.
- 다국어 지원 시 `knowledge_items`와 `messages`에 `language_code` 컬럼 확장 고려.
- 고객 익명 세션(비로그인) 정책 확정 시 `external_customer_ref` 대신 별도 `customer_sessions` 테이블 도입 검토.
