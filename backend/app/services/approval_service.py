"""Service for handling HITL approval workflow."""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from typing import List
from uuid import UUID, uuid4

from fastapi import HTTPException, status

from backend.app.repositories.conversation_repository import (
    ConversationRepository,
    MessageRecord,
)
from backend.core.database import get_supabase_client

logger = logging.getLogger(__name__)


class ApprovalService:
    """Handle agent approval workflow for AI responses."""

    def __init__(self, repository: ConversationRepository) -> None:
        self._repository = repository
        self._supabase = get_supabase_client()

    async def list_pending_approvals(self, organization_id: UUID) -> List[dict]:
        """List all AI responses pending approval for an organization.

        Returns conversations in priority order: VIP > high > standard,
        then by oldest waiting time.
        """

        # Query conversations with pending approvals
        response = (
            self._supabase.table("conversations")
            .select(
                """
                id,
                organization_id,
                priority,
                started_at,
                pending_approval_response_id,
                messages!inner(id, body, sender_type, sequence, created_at),
                ai_responses!conversations_pending_approval_response_id_fkey(
                    id, confidence, generated_at
                )
                """
            )
            .eq("organization_id", str(organization_id))
            .eq("status", "pending_approval")
            .not_.is_("pending_approval_response_id", "null")
            .order("priority", desc=True)
            .order("started_at", desc=False)
            .execute()
        )

        pending_list = []
        for conv in response.data:
            # Get customer's last message
            customer_messages = [
                msg for msg in conv.get("messages", [])
                if msg.get("sender_type") == "customer"
            ]
            if not customer_messages:
                continue

            last_customer_msg = customer_messages[-1]

            # Get AI response details
            ai_responses = conv.get("ai_responses", [])
            if not ai_responses:
                continue

            ai_response = ai_responses[0]

            # Get the AI's proposed response message
            ai_messages = [
                msg for msg in conv.get("messages", [])
                if msg.get("sender_type") == "ai"
            ]
            if not ai_messages:
                continue

            proposed_msg = ai_messages[-1]

            pending_list.append({
                "conversation_id": UUID(conv["id"]),
                "ai_response_id": UUID(ai_response["id"]),
                "customer_message": last_customer_msg.get("body", ""),
                "proposed_response": proposed_msg.get("body", ""),
                "confidence": ai_response.get("confidence", 0.0),
                "waiting_since": ai_response.get("generated_at", conv["started_at"]),
                "priority": conv["priority"],
            })

        logger.info(
            "Found %d pending approvals for organization %s",
            len(pending_list),
            organization_id,
        )
        return pending_list

    async def process_approval(
        self,
        ai_response_id: UUID,
        action: str,
        agent_id: UUID,
        submitted_text: str | None = None,
        notes: str | None = None,
    ) -> dict:
        """Process an agent's approval decision.

        Args:
            ai_response_id: UUID of the AI response being reviewed
            action: "approved", "modified", or "rejected"
            agent_id: UUID of the agent making the decision
            submitted_text: Final text to send (for "modified" action)
            notes: Optional agent notes

        Returns:
            Success response with conversation ID
        """

        if action not in ["approved", "modified", "rejected"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid action: {action}",
            )

        # Get AI response details
        ai_response = (
            self._supabase.table("ai_responses")
            .select("*, messages!inner(id, body, conversation_id)")
            .eq("id", str(ai_response_id))
            .execute()
        )

        if not ai_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"AI response {ai_response_id} not found",
            )

        ai_resp_data = ai_response.data[0]
        message_data = ai_resp_data["messages"]
        conversation_id = UUID(message_data["conversation_id"])
        original_body = message_data["body"]

        # Calculate turnaround time
        generated_at = datetime.fromisoformat(
            ai_resp_data["generated_at"].replace("Z", "+00:00")
        )
        turnaround_ms = int((datetime.now(timezone.utc) - generated_at).total_seconds() * 1000)

        # Determine final text to send
        final_text = original_body
        if action == "modified" and submitted_text:
            final_text = submitted_text

        # Create approval record
        approval_record = {
            "id": str(uuid4()),
            "ai_response_id": str(ai_response_id),
            "agent_id": str(agent_id),
            "action": action,
            "submitted_text": final_text,
            "notes": notes,
            "turnaround_ms": turnaround_ms,
        }

        self._supabase.table("approval_records").insert(approval_record).execute()

        # Update AI response status
        new_status = action  # "approved", "modified", or "rejected"
        self._supabase.table("ai_responses").update(
            {"status": new_status}
        ).eq("id", str(ai_response_id)).execute()

        # Update message body if modified
        if action == "modified" and submitted_text:
            self._supabase.table("messages").update(
                {"body": final_text}
            ).eq("id", message_data["id"]).execute()

        # Update conversation status
        if action in ["approved", "modified"]:
            # Clear pending approval and return to active
            await self._repository.update_conversation_status(
                conversation_id=conversation_id,
                new_status="active",
                pending_approval_response_id=None,
            )
            message = "Response approved and sent to customer"

        elif action == "rejected":
            # Escalate to human agent
            await self._repository.update_conversation_status(
                conversation_id=conversation_id,
                new_status="awaiting_agent",
            )
            message = "Response rejected, conversation escalated to agent"

        logger.info(
            "Processed approval: ai_response_id=%s, action=%s, agent=%s",
            ai_response_id,
            action,
            agent_id,
        )

        return {
            "success": True,
            "message": message,
            "conversation_id": conversation_id,
        }


__all__ = ["ApprovalService"]
