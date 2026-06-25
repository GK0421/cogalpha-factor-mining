"""OpenAI-compatible LLM provider with retries and concurrency control."""
import asyncio
from functools import partial

from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential
from .base import BaseLLMProvider

try:
    import openai
    from openai import APIConnectionError, APITimeoutError, RateLimitError
except ImportError as _err:
    openai = None  # type: ignore
    _IMPORT_ERR = _err
    APIConnectionError = APITimeoutError = RateLimitError = Exception  # type: ignore


class OpenAICompatibleProvider(BaseLLMProvider):
    """LLM provider backed by an OpenAI-compatible API."""

    def __init__(self, api_key: str, base_url: str, model: str, max_concurrent: int = 5,
                 max_tokens: int = 2048, timeout: int = 60, temperature: float = 0.7) -> None:
        if openai is None:
            raise ImportError("pip install openai>=1.0") from _IMPORT_ERR
        if not api_key or api_key.strip() == "***":
            raise ValueError("A valid api_key is required.")
        self.model = model
        self.temperature = temperature
        self._max_tokens = min(max_tokens, 2048)
        self._timeout = min(timeout, 60)
        self._sem = asyncio.Semaphore(max_concurrent)
        self._client = openai.AsyncOpenAI(api_key=api_key, base_url=base_url, timeout=self._timeout)

    @retry(retry=retry_if_exception_type((APIConnectionError, APITimeoutError, RateLimitError)),
           wait=wait_exponential(multiplier=1, min=2, max=10), stop=stop_after_attempt(3), reraise=True)
    async def _call(self, prompt: str, temperature: float, max_tokens: int, timeout: int) -> str:
        resp = await self._client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature, max_tokens=max_tokens, timeout=timeout,
        )
        return resp.choices[0].message.content or ""

    async def generate(self, prompt: str, temperature: float = 0.7, max_tokens: int = 2048, timeout: int = 60) -> str:
        async with self._sem:
            return await self._call(prompt, temperature, min(max_tokens, 2048), min(timeout, 60))

    def generate_sync(self, prompt: str, **kwargs) -> str:
        return asyncio.run(self.generate(prompt, **kwargs))
