"""Pydantic schemas for conversation and message resources."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


def _to_camel(value: str) -> str:
    parts = value.split("_")
    return parts[0] + "".join(word.capitalize() for word in parts[1:])


class CamelModel(BaseModel):
    """Base model that serializes attributes using camelCase."""

    model_config = ConfigDict(populate_by_name=True, alias_generator=_to_camel, extra="ignore")


class MessageAttachment(CamelModel):
    """Attachment metadata associated with a message."""

    type: Optional[str] = None
    url: Optional[HttpUrl] = None
    name: Optional[str] = None


class MessagePayload(CamelModel):
    """Payload for creating a new customer message."""

    body: str
    attachments: Optional[List[MessageAttachment]] = None


class StartConversationRequest(CamelModel):
    """Incoming payload to start a customer conversation."""

    organization_id: Optional[UUID] = Field(default=None)
    customer_id: Optional[UUID] = Field(default=None)
    metadata: Optional[Dict[str, Any]] = None
    message: MessagePayload


class AIResponseSummary(CamelModel):
    """Summary metadata about an AI-generated response."""

    id: UUID
    status: str
    confidence: float
    requires_approval: bool
    provider: Optional[str] = None
    model: Optional[str] = None
    generated_at: Optional[datetime] = None


class MessageResource(CamelModel):
    """Message representation returned in APIs."""

    id: UUID
    conversation_id: UUID
    sender_type: str
    body: str
    sequence: int
    created_at: datetime
    attachments: List[MessageAttachment] = Field(default_factory=list)
    sender_user_id: Optional[UUID] = None
    ai_response: Optional[AIResponseSummary] = None


class ConversationResource(CamelModel):
    """Conversation metadata exposed via the API."""

    id: UUID
    organization_id: Optional[UUID] = None
    customer_id: Optional[UUID] = None
    external_customer_ref: Optional[str] = None
    status: str
    channel: str
    priority: str
    started_at: datetime
    last_activity_at: datetime
    pending_approval_response_id: Optional[UUID] = None
    ended_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ConversationResponse(CamelModel):
    """Envelope returned when creating or retrieving conversations."""

    conversation: ConversationResource
    messages: List[MessageResource]
    pending_approval: bool
