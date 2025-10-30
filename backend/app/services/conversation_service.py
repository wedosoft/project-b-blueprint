"""Conversation orchestration service."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Tuple
from uuid import UUID, uuid4

from fastapi import HTTPException, status

from ..repositories.conversation_repository import (
    ConversationRecord,
    ConversationRepository,
    MessageRecord,
)
from ..schemas.conversation import (
    ConversationResponse,
    ConversationResource,
    MessageAttachment,
    MessageResource,
    StartConversationRequest,
)
from .llm_service import LLMService, ChatMessage
from .qdrant_service import QdrantService


class ConversationService:
    """Handles the conversation lifecycle with AI response generation."""

    def __init__(
        self,
        repository: ConversationRepository,
        llm_service: LLMService,
        qdrant_service: QdrantService | None = None,
    ) -> None:
        self._repository = repository
        self._llm_service = llm_service
        self._qdrant_service = qdrant_service

    async def start_conversation(
        self, payload: StartConversationRequest
    ) -> ConversationResponse:
        """Create a conversation, seed it with the customer's first message, and generate AI response."""

        # 1. 대화 및 고객 메시지 저장
        conversation_record, message_records = await self._persist_entities(payload)

        # 2. AI 응답 생성 (RAG 패턴 사용)
        ai_message = await self._generate_and_save_ai_response(
            conversation_id=conversation_record.id,
            customer_message=payload.message.body,
            organization_id=conversation_record.organization_id,
            sequence=2,
        )

        # 3. AI 메시지를 저장소에 추가
        async with self._repository._lock:
            if conversation_record.id in self._repository._messages:
                self._repository._messages[conversation_record.id].append(ai_message)
            else:
                self._repository._messages[conversation_record.id] = [ai_message]

        # 4. 모든 메시지 포함하여 응답 반환
        all_messages = message_records + [ai_message]
        response = ConversationResponse(
            conversation=self._to_conversation_resource(conversation_record),
            messages=[self._to_message_resource(record) for record in all_messages],
            pending_approval=False,  # TODO: Phase 2에서 HITL 로직 추가
        )
        return response

    async def _persist_entities(
        self, payload: StartConversationRequest
    ) -> Tuple[ConversationRecord, list[MessageRecord]]:
        now = datetime.now(timezone.utc)
        conversation_id = uuid4()
        message_id = uuid4()

        organization_id = payload.organization_id or uuid4()

        conversation = ConversationRecord(
            id=conversation_id,
            organization_id=organization_id,
            customer_id=payload.customer_id,
            status="active",
            channel="text-web",
            priority="standard",
            started_at=now,
            last_activity_at=now,
            metadata=dict(payload.metadata or {}),
        )

        message = MessageRecord(
            id=message_id,
            conversation_id=conversation_id,
            sender_type="customer",
            body=payload.message.body,
            sequence=1,
            created_at=now,
            attachments=[
                attachment.model_dump(by_alias=True, exclude_none=True)
                for attachment in (payload.message.attachments or [])
            ],
        )

        saved_conversation, saved_messages = await self._repository.create_conversation(
            conversation,
            message,
        )
        return saved_conversation, saved_messages

    async def _generate_and_save_ai_response(
        self,
        conversation_id: UUID,
        customer_message: str,
        organization_id: UUID,
        sequence: int,
    ) -> MessageRecord:
        """Generate AI response using LLM with RAG pattern (context injection)."""

        # RAG: Qdrant에서 유사 문서 검색
        context_documents = []
        if self._qdrant_service:
            try:
                search_results = await self._qdrant_service.search_similar(
                    query_text=customer_message,
                    limit=3,  # 상위 3개 유사 문서
                    score_threshold=0.3,  # 30% 이상 유사도 (실전에서는 조정 필요)
                    organization_id=str(organization_id),
                )
                context_documents = [result.content for result in search_results]
            except Exception as exc:
                # 벡터 검색 실패 시 로깅하고 계속 진행
                import logging
                logging.warning(f"Qdrant search failed, continuing without context: {exc}")

        # 시스템 프롬프트: 고객 상담 어시스턴트 역할 + 컨텍스트
        system_prompt = """당신은 전문적이고 친절한 고객 상담 어시스턴트입니다.

다음 원칙을 따라 응답하세요:
1. 항상 정중하고 공감적인 태도를 유지합니다
2. 고객의 질문을 정확히 이해하고 명확한 답변을 제공합니다
3. 필요시 추가 정보를 요청합니다
4. 답변은 간결하면서도 충분한 정보를 담습니다
5. 불확실한 정보는 추측하지 않고 확인이 필요하다고 안내합니다"""

        # 컨텍스트가 있으면 시스템 프롬프트에 추가
        if context_documents:
            context_text = "\n\n".join(
                f"참고 문서 {i+1}:\n{doc}" for i, doc in enumerate(context_documents)
            )
            system_prompt += f"\n\n[참고 정보]\n아래는 과거 유사한 문의 사항들입니다. 이를 참고하여 응답하세요:\n\n{context_text}"

        messages: list[ChatMessage] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": customer_message},
        ]

        # LLM 호출 with fallback
        fallback_text = "죄송합니다. 일시적인 오류로 응답을 생성할 수 없습니다. 잠시 후 다시 시도해 주시거나, 상담원 연결을 요청해 주세요."

        try:
            llm_result = await self._llm_service.generate_completion(
                messages=messages,
                temperature=0.7,  # 적절한 창의성
                max_output_tokens=500,
                fallback_text=fallback_text,
            )
            ai_response_body = llm_result.content
        except Exception as exc:
            # LLM 서비스 오류 시 fallback 사용
            ai_response_body = fallback_text

        # AI 메시지 레코드 생성
        now = datetime.now(timezone.utc)
        ai_message = MessageRecord(
            id=uuid4(),
            conversation_id=conversation_id,
            sender_type="ai",
            body=ai_response_body,
            sequence=sequence,
            created_at=now,
            attachments=[],
            sender_user_id=None,
        )

        return ai_message

    @staticmethod
    def _to_conversation_resource(record: ConversationRecord) -> ConversationResource:
        return ConversationResource(
            id=record.id,
            organization_id=record.organization_id,
            customer_id=record.customer_id,
            external_customer_ref=record.external_customer_ref,
            status=record.status,
            channel=record.channel,
            priority=record.priority,
            started_at=record.started_at,
            last_activity_at=record.last_activity_at,
            pending_approval_response_id=record.pending_approval_response_id,
            ended_at=record.ended_at,
            metadata=record.metadata,
        )

    @staticmethod
    def _to_message_resource(record: MessageRecord) -> MessageResource:
        return MessageResource(
            id=record.id,
            conversation_id=record.conversation_id,
            sender_type=record.sender_type,
            body=record.body,
            sequence=record.sequence,
            created_at=record.created_at,
            attachments=[
                att
                if isinstance(att, MessageAttachment)
                else MessageAttachment.model_validate(att)
                for att in record.attachments
            ],
            sender_user_id=record.sender_user_id,
            ai_response=None,
        )


__all__ = ["ConversationService"]
