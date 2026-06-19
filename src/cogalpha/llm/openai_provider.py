"""OpenAI-compatible LLM provider with retries and concurrency control."""
import asyncio
import time
from typing import Optional

from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from .base import BaseLLMProvider

# Guard import so missing ``openai`` surfaces a clean error at class instantiation time.
try:
    import openai
    from openai import (
        APIConnectionError,
        APITimeoutError,
        RateLimitError,
        AuthenticationError,
        BadRequestError,
        PermissionDeniedError,
    )
except ImportError as _import_err:  # pragma: no cover
    openai = None  # type: ignore
    _OPENAI_IMPORT_ERROR = _import_err
    # Define dummy exception types so the module remains importable even when
    # ``openai`` is not installed.  The real check happens at instantiation.
    APIConnectionError = type("APIConnectionError", (Exception,), {})  # type: ignore
    APITimeoutError = type("APITimeoutError", (Exception,), {})  # type: ignore
    RateLimitError = type("RateLimitError", (Exception,), {})  # type: ignore
    AuthenticationError = type("AuthenticationError", (Exception,), {})  # type: ignore
    BadRequestError = type("BadRequestError", (Exception,), {})  # type: ignore
    PermissionDeniedError = type("PermissionDeniedError", (Exception,), {})  # type: ignore


class OpenAICompatibleProvider(BaseLLMProvider):
    """LLM provider backed by an OpenAI-compatible API."""

    def __init__(
        self,
        api_key: str,
        base_url: str,
        model: str,
        max_concurrent: int = 5,
        max_tokens: int = 2048,
        timeout: int = 60,
        temperature: float = 0.7,
    ) -> None:
        """Initialize the provider.

        Args:
            api_key: API key for the service.
            base_url: Base URL for the OpenAI-compatible endpoint.
            model: Model identifier to use.
            max_concurrent: Maximum number of concurrent requests.
            max_tokens: Maximum tokens per generation (capped at 2048).
            timeout: Request timeout in seconds (capped at 60).
            temperature: Sampling temperature.

        Raises:
            ImportError: If the ``openai`` package is not installed.
            ValueError: If ``api_key`` is empty or a placeholder.
        """
        if openai is None:
            raise ImportError(
                "The 'openai' package is required for OpenAICompatibleProvider. "
                "Install it with: pip install openai>=1.0"
            ) from _OPENAI_IMPORT_ERROR

        if not api_key or api_key.strip() == "***":
            raise ValueError(
                "A valid 'api_key' must be provided for OpenAICompatibleProvider."
            )

        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.max_tokens = min(max_tokens, 2048)
        self.timeout = min(timeout, 60)
        self.temperature = temperature
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._client = openai.AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=self.timeout,
        )

    @retry(
        retry=retry_if_exception_type(
            (APIConnectionError, APITimeoutError, RateLimitError)
        ),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        stop=stop_after_attempt(3),
        reraise=True,
    )
    async def _generate_with_retry(
        self,
        prompt: str,
        temperature: float,
        max_tokens: int,
        timeout: int,
    ) -> str:
        """Internal generation with retry logic."""
        response = await self._client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=timeout,
        )
        return response.choices[0].message.content or ""

    async def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        timeout: int = 60,
    ) -> str:
        """Generate text via the OpenAI-compatible API.

        Args:
            prompt: The prompt to send to the model.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens to generate.
            timeout: Request timeout in seconds.

        Returns:
            Generated text string.

        Raises:
            AuthenticationError: On invalid API credentials.
            BadRequestError: On malformed requests.
            PermissionDeniedError: On insufficient permissions.
        """
        max_tokens = min(max_tokens, 2048)
        timeout = min(timeout, 60)

        async with self._semaphore:
            return await self._generate_with_retry(
                prompt=prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=timeout,
            )

    def generate_sync(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        timeout: int = 60,
    ) -> str:
        """Synchronous wrapper for :meth:`generate`."""
        return asyncio.run(
            self.generate(
                prompt=prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=timeout,
            )
        )
