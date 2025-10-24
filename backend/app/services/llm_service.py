"""LLM orchestration with retry, fallback, and unified response typing."""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass
from typing import List, Literal, Sequence, Tuple, TypedDict

from openai import AsyncOpenAI
from openai.types.chat import ChatCompletion, ChatCompletionMessageParam

from core.config import get_settings

logger = logging.getLogger(__name__)

LLMProvider = Literal["openai", "fallback"]


class ChatMessage(TypedDict):
    """Simple chat message payload."""

    role: Literal["system", "user", "assistant"]
    content: str


@dataclass(slots=True)
class LLMUsage:
    """Token usage accounting returned by providers."""

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


@dataclass(slots=True)
class LLMResult:
    """Unified generated response from any provider."""

    provider: LLMProvider
    model: str
    content: str
    latency_ms: int
    usage: LLMUsage | None = None


class LLMGenerationError(RuntimeError):
    """Raised when provider calls fail and no fallback is available."""

    def __init__(self, errors: Sequence[BaseException]) -> None:
        self.errors = list(errors)
        message = "All configured LLM providers failed."
        super().__init__(message)


class LLMService:
    """Orchestrates LLM calls with retry and optional provider fallback."""

    def __init__(
        self,
        *,
        max_retries: int = 2,
        retry_delay_seconds: float = 1.0,
    ) -> None:
        self._settings = get_settings()
        self._max_retries = max(0, max_retries)
        self._retry_delay_seconds = retry_delay_seconds

        self._primary_provider: LLMProvider = self._settings.llm.provider  # type: ignore[assignment]

        self._openai_client: AsyncOpenAI | None = None
        if self._settings.llm.openai_api_key:
            self._openai_client = AsyncOpenAI(
                api_key=self._settings.llm.openai_api_key.get_secret_value(),
                timeout=self._settings.llm.request_timeout_seconds,
            )

    async def generate_completion(
        self,
        messages: Sequence[ChatMessage],
        *,
        model: str | None = None,
        temperature: float = 0.3,
        top_p: float = 0.9,
        max_output_tokens: int = 600,
        fallback_text: str | None = None,
    ) -> LLMResult:
        """Generate a response using the configured providers.

        Attempts the primary provider first, then optional fallback provider(s).
        Returns `fallback_text` if provided and all providers fail.
        """
        attempts: List[BaseException] = []
        providers = self._provider_sequence()

        for provider in providers:
            try:
                result = await self._call_provider(
                    provider=provider,
                    messages=messages,
                    model_override=model,
                    temperature=temperature,
                    top_p=top_p,
                    max_output_tokens=max_output_tokens,
                )
                return result
            except Exception as exc:  # pragma: no cover - network errors are unpredictable
                attempts.append(exc)
                logger.warning("LLM provider %s failed: %s", provider, exc)
                await asyncio.sleep(self._retry_delay_seconds)

        if fallback_text is not None:
            logger.info("Using static fallback response after provider failures.")
            return LLMResult(
                provider="fallback",
                model="static-fallback",
                content=fallback_text,
                latency_ms=0,
                usage=None,
            )

        raise LLMGenerationError(attempts)

    async def _call_provider(
        self,
        *,
        provider: LLMProvider,
        messages: Sequence[ChatMessage],
        model_override: str | None,
        temperature: float,
        top_p: float,
        max_output_tokens: int,
    ) -> LLMResult:
        """Dispatch to a provider-specific implementation with retries."""
        last_error: Exception | None = None
        for attempt in range(self._max_retries + 1):
            try:
                if provider == "openai":
                    return await self._invoke_openai(
                        messages=messages,
                        model_override=model_override,
                        temperature=temperature,
                        top_p=top_p,
                        max_output_tokens=max_output_tokens,
                    )
                raise RuntimeError(f"Unsupported provider: {provider}")
            except Exception as exc:  # pragma: no cover - depends on network
                last_error = exc
                if attempt < self._max_retries:
                    await asyncio.sleep(self._retry_delay_seconds)
        if last_error:
            raise last_error
        raise RuntimeError(f"Provider {provider!r} failed without exception context.")

    def _provider_sequence(self) -> Tuple[LLMProvider, ...]:
        sequence: List[LLMProvider] = []

        if self._primary_provider == "openai" and self._openai_client:
            sequence.append("openai")

        if "openai" not in sequence and self._openai_client:
            sequence.append("openai")

        return tuple(sequence)

    async def _invoke_openai(
        self,
        *,
        messages: Sequence[ChatMessage],
        model_override: str | None,
        temperature: float,
        top_p: float,
        max_output_tokens: int,
    ) -> LLMResult:
        if self._openai_client is None or not self._settings.llm.openai_api_key:
            raise RuntimeError("OpenAI client not configured.")

        model_name = model_override or self._settings.llm.default_model
        payload: List[ChatCompletionMessageParam] = [
            {"role": msg["role"], "content": msg["content"]} for msg in messages
        ]

        start = time.perf_counter()
        response: ChatCompletion = await self._openai_client.chat.completions.create(
            model=model_name,
            messages=payload,
            temperature=temperature,
            top_p=top_p,
            max_tokens=max_output_tokens,
        )
        latency_ms = int((time.perf_counter() - start) * 1000)

        choice = response.choices[0]
        content_parts = choice.message.content or ""
        text = (
            content_parts if isinstance(content_parts, str) else "".join(content_parts)
        )
        usage = None
        if response.usage:
            usage = LLMUsage(
                prompt_tokens=response.usage.prompt_tokens or 0,
                completion_tokens=response.usage.completion_tokens or 0,
                total_tokens=response.usage.total_tokens or 0,
            )

        return LLMResult(
            provider="openai",
            model=response.model or model_name,
            content=text,
            latency_ms=latency_ms,
            usage=usage,
        )
