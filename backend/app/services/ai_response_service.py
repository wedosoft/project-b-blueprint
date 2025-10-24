"""AI response generation with confidence scoring and knowledge base integration."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import List
from uuid import UUID, uuid4

from backend.app.services.llm_service import ChatMessage, LLMService
from backend.app.services.vector_search_service import (
    KnowledgeSearchResult,
    VectorSearchService,
)

logger = logging.getLogger(__name__)

# Confidence threshold for requiring human approval
CONFIDENCE_THRESHOLD = 0.80


@dataclass(slots=True)
class GeneratedResponse:
    """Complete AI-generated response with metadata."""

    response_id: UUID
    message_body: str
    confidence: float
    requires_approval: bool
    llm_provider: str
    llm_model: str
    prompt_tokens: int
    completion_tokens: int
    latency_ms: int
    knowledge_sources: List[dict]


class AIResponseService:
    """Generate AI responses with knowledge base and confidence scoring."""

    def __init__(
        self,
        llm_service: LLMService | None = None,
        vector_service: VectorSearchService | None = None,
    ) -> None:
        self._llm_service = llm_service or LLMService()
        self._vector_service = vector_service or VectorSearchService()

    async def generate_response(
        self,
        conversation_id: UUID,
        organization_id: UUID,
        customer_message: str,
        conversation_history: List[dict] | None = None,
    ) -> GeneratedResponse:
        """Generate an AI response for a customer message.

        Args:
            conversation_id: Current conversation UUID
            organization_id: Organization UUID for knowledge filtering
            customer_message: Latest message from customer
            conversation_history: Previous messages in conversation

        Returns:
            GeneratedResponse with confidence score and approval requirement
        """

        # 1. Search knowledge base for relevant context
        knowledge_results = await self._vector_service.search_knowledge_base(
            query=customer_message,
            organization_id=organization_id,
            limit=3,
            score_threshold=0.7,
        )

        # 2. Build context from knowledge base
        context_parts = []
        knowledge_sources = []

        for result in knowledge_results:
            context_parts.append(f"- {result.title}: {result.content}")
            knowledge_sources.append({
                "knowledge_item_id": str(result.knowledge_item_id),
                "title": result.title,
                "score": result.score,
                "source_uri": result.source_uri,
            })

        knowledge_context = "\n".join(context_parts) if context_parts else "No specific knowledge base articles found."

        # 3. Build conversation history
        history_text = ""
        if conversation_history:
            for msg in conversation_history[-5:]:  # Last 5 messages
                role = msg.get("sender_type", "unknown")
                body = msg.get("body", "")
                history_text += f"{role}: {body}\n"

        # 4. Create system prompt
        system_prompt = f"""You are a helpful customer support AI assistant.

Your job is to answer customer questions accurately and professionally.

Available Knowledge Base Context:
{knowledge_context}

Recent Conversation History:
{history_text}

Instructions:
- Provide clear, accurate, and helpful responses
- Use information from the knowledge base when relevant
- If you're not certain about an answer, be honest about it
- Keep responses concise but complete
- Be professional and empathetic"""

        # 5. Generate LLM response
        messages: List[ChatMessage] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": customer_message},
        ]

        llm_result = await self._llm_service.generate_completion(
            messages=messages,
            temperature=0.3,
            max_output_tokens=600,
            fallback_text="I apologize, but I'm having trouble processing your request right now. A human agent will assist you shortly.",
        )

        # 6. Calculate confidence score
        confidence = self._calculate_confidence(
            knowledge_results=knowledge_results,
            llm_provider=llm_result.provider,
        )

        # 7. Determine if approval is required
        requires_approval = confidence < CONFIDENCE_THRESHOLD

        logger.info(
            "Generated AI response for conversation %s: confidence=%.2f, requires_approval=%s",
            conversation_id,
            confidence,
            requires_approval,
        )

        return GeneratedResponse(
            response_id=uuid4(),
            message_body=llm_result.content,
            confidence=confidence,
            requires_approval=requires_approval,
            llm_provider=llm_result.provider,
            llm_model=llm_result.model,
            prompt_tokens=llm_result.usage.prompt_tokens if llm_result.usage else 0,
            completion_tokens=llm_result.usage.completion_tokens if llm_result.usage else 0,
            latency_ms=llm_result.latency_ms,
            knowledge_sources=knowledge_sources,
        )

    def _calculate_confidence(
        self,
        knowledge_results: List[KnowledgeSearchResult],
        llm_provider: str,
    ) -> float:
        """Calculate confidence score for the generated response.

        For MVP, confidence is based primarily on knowledge base search quality.
        Future enhancements could include:
        - LLM-based confidence scoring
        - Historical accuracy metrics
        - Topic classification confidence
        - Response quality analysis

        Args:
            knowledge_results: Vector search results from knowledge base
            llm_provider: Which LLM provider was used

        Returns:
            Confidence score between 0.0 and 1.0
        """

        # Base confidence starts at 0.5
        confidence = 0.50

        # Boost confidence based on knowledge base matches
        if knowledge_results:
            # Use the top result's score as primary indicator
            top_score = knowledge_results[0].score

            # High quality match (>0.85) significantly boosts confidence
            if top_score > 0.85:
                confidence = min(0.95, 0.60 + (top_score * 0.35))
            # Good match (>0.75) moderately boosts confidence
            elif top_score > 0.75:
                confidence = 0.50 + (top_score * 0.30)
            # Fair match (>0.70) slightly boosts confidence
            else:
                confidence = 0.50 + (top_score * 0.20)

            # Additional boost for multiple relevant results
            if len(knowledge_results) >= 2:
                confidence = min(1.0, confidence + 0.05)
            if len(knowledge_results) >= 3:
                confidence = min(1.0, confidence + 0.03)

        # Slight penalty if using fallback provider
        if llm_provider == "fallback":
            confidence *= 0.5

        # Ensure confidence is within bounds
        return max(0.0, min(1.0, confidence))


__all__ = ["AIResponseService", "GeneratedResponse", "CONFIDENCE_THRESHOLD"]
