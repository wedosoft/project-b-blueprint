"""Conversation orchestration service."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Tuple
from uuid import UUID, uuid4

from fastapi import HTTPException, status

from backend.app.repositories.conversation_repository import (
    ConversationRecord,
    ConversationRepository,
    MessageRecord,
)
from backend.app.schemas.conversation import (
    ConversationResponse,
    ConversationResource,
    MessageAttachment,
    MessageResource,
    StartConversationRequest,
)


class ConversationService:
    """Handles the conversation lifecycle prior to persistence integration."""

    def __init__(self, repository: ConversationRepository) -> None:
        self._repository = repository

    async def start_conversation(
        self, payload: StartConversationRequest
    ) -> ConversationResponse:
        """Create a conversation and seed it with the customer's first message."""

        conversation_record, message_records = await self._persist_entities(payload)
        response = ConversationResponse(
            conversation=self._to_conversation_resource(conversation_record),
            messages=[self._to_message_resource(record) for record in message_records],
            pending_approval=False,
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
