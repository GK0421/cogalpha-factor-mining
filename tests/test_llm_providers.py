"""Tests for LLM provider modules."""
import ast

import pytest

from cogalpha.llm.mock_provider import MockLLMProvider, MOCK_FACTORS


def test_mock_provider_returns_string_with_function_tags():
    """Mock generate() should return a string containing <function tags."""
    provider = MockLLMProvider()
    result = provider.generate_sync("generate some factors")
    assert "<function" in result


def test_mock_provider_returns_at_least_two_factors():
    """Mock output should contain at least 2 factor definitions."""
    provider = MockLLMProvider()
    result = provider.generate_sync("generate some factors")
    # Count occurrences of function definition lines inside the tags
    func_defs = [line for line in result.splitlines() if line.strip().startswith("def ")]
    assert len(func_defs) >= 2


def test_mock_factors_are_syntactically_valid():
    """Each factor code block between tags should be valid Python."""
    provider = MockLLMProvider()
    result = provider.generate_sync("generate some factors")

    # Extract code blocks between <function N> and </function N>
    lines = result.splitlines()
    in_block = False
    blocks = []
    current_block = []

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("<function") and not stripped.startswith("</function"):
            in_block = True
            current_block = []
        elif stripped.startswith("</function"):
            in_block = False
            if current_block:
                blocks.append("\n".join(current_block))
            current_block = []
        elif in_block:
            current_block.append(line)

    assert len(blocks) >= 2, "Expected at least 2 factor code blocks"

    for block in blocks:
        try:
            ast.parse(block)
        except SyntaxError as exc:
            pytest.fail(f"Syntax error in mock factor block:\n{block}\nError: {exc}")


class TestOpenAICompatibleProvider:
    """Tests for OpenAICompatibleProvider."""

    def test_raises_on_missing_api_key(self):
        """Provider should raise ValueError when api_key is empty or placeholder."""
        from cogalpha.llm.openai_provider import OpenAICompatibleProvider

        with pytest.raises(ValueError, match="api_key"):
            OpenAICompatibleProvider(
                api_key="",
                base_url="https://api.openai.com/v1",
                model="gpt-4",
            )

        with pytest.raises(ValueError, match="api_key"):
            OpenAICompatibleProvider(
                api_key="***",
                base_url="https://api.openai.com/v1",
                model="gpt-4",
            )
