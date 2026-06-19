"""Base LLM provider interface."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
import asyncio
import time


@dataclass
class GenerationResult:
    """Result of a single LLM generation call."""
    raw_text: str
    usage_tokens: int = 0
    latency_ms: float = 0.0


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        timeout: int = 60,
    ) -> str:
        """Generate text asynchronously.

        Args:
            prompt: The prompt to send to the model.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens to generate.
            timeout: Request timeout in seconds.

        Returns:
            Generated text string.
        """

    def generate_sync(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        timeout: int = 60,
    ) -> str:
        """Synchronous wrapper around ``generate``.

        Args:
            prompt: The prompt to send to the model.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens to generate.
            timeout: Request timeout in seconds.

        Returns:
            Generated text string.
        """
        return asyncio.run(self.generate(prompt, temperature, max_tokens, timeout))
