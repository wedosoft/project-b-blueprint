"""HTTP routes for HITL approval workflow."""

from __future__ import annotations

from functools import lru_cache
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from ...repositories.conversation_repository import ConversationRepository
from ...services.approval_service import ApprovalService


router = APIRouter(prefix="/v1/approvals", tags=["Approvals"])


class PendingApprovalResponse(BaseModel):
    """A conversation pending approval."""

    conversation_id: UUID
    ai_response_id: UUID
    customer_message: str
    proposed_response: str
    confidence: float
    waiting_since: str
    priority: str


class ApprovalActionRequest(BaseModel):
    """Request to approve, modify, or reject an AI response."""

    action: str  # "approved", "modified", "rejected"
    agent_id: UUID
    submitted_text: str | None = None
    notes: str | None = None


class ApprovalActionResponse(BaseModel):
    """Response after processing an approval action."""

    success: bool
    message: str
    conversation_id: UUID


@lru_cache(maxsize=1)
def get_approval_service() -> ApprovalService:
    return ApprovalService(repository=ConversationRepository())


@router.get(
    "/pending",
    response_model=List[PendingApprovalResponse],
    summary="List pending approvals",
    description="Retrieve all AI responses awaiting agent review, ordered by priority and wait time.",
)
async def list_pending_approvals(
    organization_id: UUID,
    service: ApprovalService = Depends(get_approval_service),
) -> List[PendingApprovalResponse]:
    """Get all pending approvals for an organization."""
    try:
        return await service.list_pending_approvals(organization_id)
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="승인 대기 목록을 조회하는 중 오류가 발생했습니다.",
        ) from exc


@router.post(
    "/{ai_response_id}/approve",
    response_model=ApprovalActionResponse,
    summary="Approve AI response",
    description="Approve an AI response to be sent to the customer.",
)
async def approve_response(
    ai_response_id: UUID,
    payload: ApprovalActionRequest,
    service: ApprovalService = Depends(get_approval_service),
) -> ApprovalActionResponse:
    """Approve an AI response."""
    try:
        return await service.process_approval(
            ai_response_id=ai_response_id,
            action=payload.action,
            agent_id=payload.agent_id,
            submitted_text=payload.submitted_text,
            notes=payload.notes,
        )
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="승인 처리 중 오류가 발생했습니다.",
        ) from exc
