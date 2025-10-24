"""Conversation orchestration service."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import List, Tuple
from uuid import UUID, uuid4

from fastapi import HTTPException, status

from ..repositories.conversation_repository import (
    AIResponseRecord,
    ConversationRecord,
    ConversationRepository,
    MessageRecord,
)
from ..schemas.conversation import (
    AIResponseSummary,
    ConversationResponse,
    ConversationResource,
    MessageAttachment,
    MessageResource,
    StartConversationRequest,
)
from .ai_response_service import AIResponseService

logger = logging.getLogger(__name__)


class ConversationService:
    """Handles the conversation lifecycle with AI response generation."""

    def __init__(
        self,
        repository: ConversationRepository,
        ai_service: AIResponseService | None = None,
    ) -> None:
        self._repository = repository
        self._ai_service = ai_service or AIResponseService()

    async def start_conversation(
        self, payload: StartConversationRequest
    ) -> ConversationResponse:
        """Create a conversation and seed it with the customer's first message.

        Automatically generates an AI response to the first message.
        """

        conversation_record, message_records = await self._persist_entities(payload)

        # Generate AI response to the first message
        ai_response = await self._ai_service.generate_response(
            conversation_id=conversation_record.id,
            organization_id=conversation_record.organization_id or uuid4(),
            customer_message=payload.message.body,
            conversation_history=[],
        )

        # Create AI message record
        ai_message = MessageRecord(
            id=uuid4(),
            conversation_id=conversation_record.id,
            sender_type="ai",
            body=ai_response.message_body,
            sequence=2,
            created_at=datetime.now(timezone.utc),
            attachments=[],
        )

        # Create AI response record
        ai_response_record = AIResponseRecord(
            id=ai_response.response_id,
            conversation_id=conversation_record.id,
            message_id=ai_message.id,
            llm_provider=ai_response.llm_provider,
            llm_model=ai_response.llm_model,
            confidence=ai_response.confidence,
            requires_approval=ai_response.requires_approval,
            status="pending" if ai_response.requires_approval else "approved",
            knowledge_sources=ai_response.knowledge_sources,
            prompt_tokens=ai_response.prompt_tokens,
            completion_tokens=ai_response.completion_tokens,
            latency_ms=ai_response.latency_ms,
        )

        # Save AI message with response metadata
        await self._repository.add_message(ai_message, ai_response_record)
        message_records.append(ai_message)

        # Update conversation status if approval is required
        if ai_response.requires_approval:
            await self._repository.update_conversation_status(
                conversation_id=conversation_record.id,
                new_status="pending_approval",
                pending_approval_response_id=ai_response.response_id,
            )
            conversation_record.status = "pending_approval"
            conversation_record.pending_approval_response_id = ai_response.response_id

        logger.info(
            "Started conversation %s with AI response (confidence=%.2f, requires_approval=%s)",
            conversation_record.id,
            ai_response.confidence,
            ai_response.requires_approval,
        )

        response = ConversationResponse(
            conversation=self._to_conversation_resource(conversation_record),
            messages=[
                self._to_message_resource(record, ai_response_record if record.id == ai_message.id else None)
                for record in message_records
            ],
            pending_approval=ai_response.requires_approval,
        )
        return response

    async def get_conversation(self, conversation_id: UUID) -> ConversationResponse:
        """Retrieve a conversation with all its messages."""

        conversation = await self._repository.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Conversation {conversation_id} not found",
            )

        messages = await self._repository.list_messages(conversation_id)

        return ConversationResponse(
            conversation=self._to_conversation_resource(conversation),
            messages=[self._to_message_resource(msg) for msg in messages],
            pending_approval=conversation.pending_approval_response_id is not None,
        )

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
    def _to_message_resource(
        record: MessageRecord,
        ai_response: AIResponseRecord | None = None,
    ) -> MessageResource:
        ai_summary = None
        if ai_response:
            ai_summary = AIResponseSummary(
                id=ai_response.id,
                status=ai_response.status,
                confidence=ai_response.confidence,
                requires_approval=ai_response.requires_approval,
                provider=ai_response.llm_provider,
                model=ai_response.llm_model,
                generated_at=ai_response.generated_at,
            )

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
            ai_response=ai_summary,
        )


__all__ = ["ConversationService"]
