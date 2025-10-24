"""HTTP routes for conversation lifecycle."""

from __future__ import annotations

from functools import lru_cache

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
)
async def start_conversation(
    payload: StartConversationRequest,
    service: ConversationService = Depends(get_conversation_service),
) -> ConversationResponse:
    try:
        return await service.start_conversation(payload)
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - defensive guardrail
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="대화를 생성하는 중 오류가 발생했습니다.",
        ) from exc
