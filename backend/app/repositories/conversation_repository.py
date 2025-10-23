"""Repository abstraction for conversation persistence.

The current implementation maintains an in-memory store so that contract tests
can exercise the API without an actual database connection. The API mirrors the
operations we plan to support once Supabase integration is wired in.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Tuple
from uuid import UUID


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


class ConversationRepository:
    """Persist conversations and messages.

    Replaced with a database-backed implementation in future phases.
    """

    def __init__(self) -> None:
        self._conversations: Dict[UUID, ConversationRecord] = {}
        self._messages: Dict[UUID, List[MessageRecord]] = {}
        self._lock = asyncio.Lock()

    async def create_conversation(
        self,
        conversation: ConversationRecord,
        first_message: MessageRecord,
    ) -> Tuple[ConversationRecord, List[MessageRecord]]:
        """Persist a new conversation along with its first message."""

        async with self._lock:
            self._conversations[conversation.id] = conversation
            messages = [first_message]
            self._messages[conversation.id] = messages
            return conversation, messages

    async def list_messages(self, conversation_id: UUID) -> List[MessageRecord]:
        """Return messages associated with a conversation."""

        async with self._lock:
            return list(self._messages.get(conversation_id, ()))


__all__ = [
    "ConversationRecord",
    "MessageRecord",
    "ConversationRepository",
]
