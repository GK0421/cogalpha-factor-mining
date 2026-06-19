"""Prompt templates and composition utilities for CogAlpha agents."""

from __future__ import annotations

# Base system prompt injected before any level-specific prompt.
BASE_SYSTEM_PROMPT = """\
You are an elite quantitative finance researcher operating inside the CogAlpha factor mining engine.

Your goal is to generate novel, statistically robust alpha factors from OHLCV market data. Each factor must be:
- Computationally efficient (no heavy loops or nested O(N^2) operations).
- Free of look-ahead bias (no future data leakage).
- Expressible as a single Python function that returns a pandas Series.
- Intuitive in its financial interpretation.

When generating code, always:
1. Use vectorized pandas/NumPy operations.
2. Handle edge cases (e.g., insufficient data, NaN values) gracefully.
3. Comment the financial logic briefly.
4. Return a named Series aligned to the input index.

The CogAlpha engine rewards creative, non-obvious factor ideas that generalize across market regimes."""


# Mode-to-creativity mapping (controls prompt variation and expected LLM temperature).
MODE_DESCRIPTIONS = {
    "mild": "Conservative, well-established factor types. Favor robustness and simplicity.",
    "moderate": "Balanced creativity. Blend known techniques with novel twists.",
    "creative": "High novelty. Explore unconventional combinations and non-linear interactions.",
    "divergent": "Maximum divergence. Break standard assumptions and invent new primitives.",
    "concrete": "Strict, implementable logic. Focus on precise, deterministic transformations.",
}


def compose_system_prompt(mode: str = "moderate") -> str:
    """Compose the full system prompt string for a given generation mode.

    Args:
        mode: One of mild, moderate, creative, divergent, concrete.

    Returns:
        The combined system prompt text.
    """
    mode_desc = MODE_DESCRIPTIONS.get(mode, MODE_DESCRIPTIONS["moderate"])
    return f"{BASE_SYSTEM_PROMPT}\n\nGeneration mode: {mode}\nMode guidance: {mode_desc}"


def build_prompt_payload(
    agent_id: str,
    mode: str,
    invalid_cases: str,
    elite_ideas: str,
    temperature: float,
) -> dict:
    """Build the variable payload dictionary for Jinja2 rendering.

    Args:
        agent_id: Identifier of the requesting agent.
        mode: Generation mode string.
        invalid_cases: Summary of previously failed factor ideas.
        elite_ideas: Brief summary of elite factor ideas.
        temperature: Target temperature for the LLM call.

    Returns:
        Dictionary with all variables expected by the Jinja2 templates.
    """
    return {
        "agent_id": agent_id,
        "mode": mode,
        "invalid_cases": invalid_cases,
        "elite_ideas": elite_ideas,
        "temperature": temperature,
        "mode_description": MODE_DESCRIPTIONS.get(mode, MODE_DESCRIPTIONS["moderate"]),
    }
