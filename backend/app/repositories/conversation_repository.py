"""Repository abstraction for conversation persistence."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Tuple
from uuid import UUID

from supabase import Client

from backend.core.database import get_supabase_client


@dataclass(slots=True)
class ConversationRecord:
    """Internal representation of a conversation."""

    id: UUID
    organization_id: UUID | None
    customer_id: UUID | None
    status: str
    channel: str
    priority: str
    started_at: datetime
    last_activity_at: datetime
    metadata: Dict[str, object]
    pending_approval_response_id: UUID | None = None
    external_customer_ref: str | None = None
    ended_at: datetime | None = None


@dataclass(slots=True)
class MessageRecord:
    """Internal representation of a message."""

    id: UUID
    conversation_id: UUID
    sender_type: str
    body: str
    sequence: int
    created_at: datetime
    attachments: List[Dict[str, object]] = field(default_factory=list)
    sender_user_id: UUID | None = None


@dataclass(slots=True)
class AIResponseRecord:
    """Internal representation of an AI response."""

    id: UUID
    conversation_id: UUID
    message_id: UUID
    llm_provider: str
    llm_model: str
    confidence: float
    requires_approval: bool
    status: str
    knowledge_sources: List[Dict[str, object]]
    prompt_tokens: int
    completion_tokens: int
    latency_ms: int
    error_reason: str | None = None
    generated_at: datetime | None = None


class ConversationRepository:
    """Persist conversations and messages using Supabase."""

    def __init__(self, client: Client | None = None) -> None:
        self._client = client or get_supabase_client()
        self._lock = asyncio.Lock()

    async def create_conversation(
        self,
        conversation: ConversationRecord,
        first_message: MessageRecord,
    ) -> Tuple[ConversationRecord, List[MessageRecord]]:
        """Persist a new conversation along with its first message."""

        async with self._lock:
            # Insert conversation
            conv_data = {
                "id": str(conversation.id),
                "organization_id": str(conversation.organization_id) if conversation.organization_id else None,
                "customer_user_id": str(conversation.customer_id) if conversation.customer_id else None,
                "external_customer_ref": conversation.external_customer_ref,
                "channel": conversation.channel,
                "status": conversation.status,
                "priority": conversation.priority,
                "started_at": conversation.started_at.isoformat(),
                "last_activity_at": conversation.last_activity_at.isoformat(),
                "metadata": conversation.metadata,
            }

            self._client.table("conversations").insert(conv_data).execute()

            # Insert first message
            msg_data = {
                "id": str(first_message.id),
                "conversation_id": str(first_message.conversation_id),
                "sender_type": first_message.sender_type,
                "sender_user_id": str(first_message.sender_user_id) if first_message.sender_user_id else None,
                "body": first_message.body,
                "attachments": first_message.attachments,
                "sequence": first_message.sequence,
                "created_at": first_message.created_at.isoformat(),
            }

            self._client.table("messages").insert(msg_data).execute()

            return conversation, [first_message]

    async def list_messages(self, conversation_id: UUID) -> List[MessageRecord]:
        """Return messages associated with a conversation."""

        response = (
            self._client.table("messages")
            .select("*")
            .eq("conversation_id", str(conversation_id))
            .order("sequence")
            .execute()
        )

        messages = []
        for row in response.data:
            messages.append(
                MessageRecord(
                    id=UUID(row["id"]),
                    conversation_id=UUID(row["conversation_id"]),
                    sender_type=row["sender_type"],
                    body=row["body"],
                    sequence=row["sequence"],
                    created_at=datetime.fromisoformat(row["created_at"].replace("Z", "+00:00")),
                    attachments=row.get("attachments", []),
                    sender_user_id=UUID(row["sender_user_id"]) if row.get("sender_user_id") else None,
                )
            )
        return messages

    async def get_conversation(self, conversation_id: UUID) -> ConversationRecord | None:
        """Retrieve a conversation by ID."""

        response = (
            self._client.table("conversations")
            .select("*")
            .eq("id", str(conversation_id))
            .execute()
        )

        if not response.data:
            return None

        row = response.data[0]
        return ConversationRecord(
            id=UUID(row["id"]),
            organization_id=UUID(row["organization_id"]) if row.get("organization_id") else None,
            customer_id=UUID(row["customer_user_id"]) if row.get("customer_user_id") else None,
            external_customer_ref=row.get("external_customer_ref"),
            status=row["status"],
            channel=row["channel"],
            priority=row["priority"],
            started_at=datetime.fromisoformat(row["started_at"].replace("Z", "+00:00")),
            last_activity_at=datetime.fromisoformat(row["last_activity_at"].replace("Z", "+00:00")),
            pending_approval_response_id=UUID(row["pending_approval_response_id"]) if row.get("pending_approval_response_id") else None,
            ended_at=datetime.fromisoformat(row["ended_at"].replace("Z", "+00:00")) if row.get("ended_at") else None,
            metadata=row.get("metadata", {}),
        )

    async def add_message(
        self,
        message: MessageRecord,
        ai_response: AIResponseRecord | None = None,
    ) -> MessageRecord:
        """Add a new message to a conversation."""

        async with self._lock:
            msg_data = {
                "id": str(message.id),
                "conversation_id": str(message.conversation_id),
                "sender_type": message.sender_type,
                "sender_user_id": str(message.sender_user_id) if message.sender_user_id else None,
                "body": message.body,
                "attachments": message.attachments,
                "sequence": message.sequence,
                "created_at": message.created_at.isoformat(),
            }

            self._client.table("messages").insert(msg_data).execute()

            # If there's an AI response, insert it
            if ai_response:
                ai_data = {
                    "id": str(ai_response.id),
                    "conversation_id": str(ai_response.conversation_id),
                    "message_id": str(ai_response.message_id),
                    "llm_provider": ai_response.llm_provider,
                    "llm_model": ai_response.llm_model,
                    "confidence": float(ai_response.confidence),
                    "requires_approval": ai_response.requires_approval,
                    "status": ai_response.status,
                    "knowledge_sources": ai_response.knowledge_sources,
                    "prompt_tokens": ai_response.prompt_tokens,
                    "completion_tokens": ai_response.completion_tokens,
                    "latency_ms": ai_response.latency_ms,
                    "error_reason": ai_response.error_reason,
                }

                self._client.table("ai_responses").insert(ai_data).execute()

                # Update message with ai_response_id
                self._client.table("messages").update(
                    {"ai_response_id": str(ai_response.id)}
                ).eq("id", str(message.id)).execute()

            # Update conversation last_activity_at
            self._client.table("conversations").update(
                {"last_activity_at": message.created_at.isoformat()}
            ).eq("id", str(message.conversation_id)).execute()

            return message

    async def update_conversation_status(
        self,
        conversation_id: UUID,
        new_status: str,
        pending_approval_response_id: UUID | None = None,
    ) -> None:
        """Update conversation status."""

        update_data = {"status": new_status}
        if pending_approval_response_id is not None:
            update_data["pending_approval_response_id"] = str(pending_approval_response_id)

        self._client.table("conversations").update(update_data).eq(
            "id", str(conversation_id)
        ).execute()


__all__ = [
    "ConversationRecord",
    "MessageRecord",
    "AIResponseRecord",
    "ConversationRepository",
]
