"""HTTP routes for conversation lifecycle."""

from __future__ import annotations

from functools import lru_cache
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from ...repositories.conversation_repository import ConversationRepository
from ...schemas.conversation import (
    ConversationResponse,
    StartConversationRequest,
)
from ...services.conversation_service import ConversationService


router = APIRouter(prefix="/v1/conversations", tags=["Conversations"])


@lru_cache(maxsize=1)
def get_conversation_repository() -> ConversationRepository:
    return ConversationRepository()


@lru_cache(maxsize=1)
def get_conversation_service() -> ConversationService:
    return ConversationService(repository=get_conversation_repository())


@router.post(
    "",
    response_model=ConversationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start a new conversation",
    description="Create a new conversation with a customer's initial message. "
                "The system will automatically generate an AI response.",
)
async def start_conversation(
    payload: StartConversationRequest,
    service: ConversationService = Depends(get_conversation_service),
) -> ConversationResponse:
    """Create a new conversation and generate initial AI response."""
    try:
        return await service.start_conversation(payload)
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - defensive guardrail
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="대화를 생성하는 중 오류가 발생했습니다.",
        ) from exc


@router.get(
    "/{conversation_id}",
    response_model=ConversationResponse,
    status_code=status.HTTP_200_OK,
    summary="Get conversation details",
    description="Retrieve a conversation with all its messages and metadata.",
)
async def get_conversation(
    conversation_id: UUID,
    service: ConversationService = Depends(get_conversation_service),
) -> ConversationResponse:
    """Retrieve a conversation by ID with all messages."""
    try:
        return await service.get_conversation(conversation_id)
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="대화를 조회하는 중 오류가 발생했습니다.",
        ) from exc
