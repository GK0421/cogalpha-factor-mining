import pytest

from cogalpha.factors.parser import FactorParser


class TestFactorParser:

    def test_extract_function_blocks(self):
        raw = (
            "Here is your factor:\n"
            "<function 1>\n"
            "def my_factor(df):\n"
            "    return df['close'] / df['open']\n"
            "</function 1>\n"
            "Let me know if you need more."
        )
        results = FactorParser.parse(raw)
        assert len(results) == 1
        assert "def my_factor(df):" in results[0]

    def test_multiple_function_blocks(self):
        raw = (
            "<function 1>\n"
            "def a(df): return 1\n"
            "</function 1>\n"
            "<function 2>\n"
            "def b(df): return 2\n"
            "</function 2>"
        )
        results = FactorParser.parse(raw)
        assert len(results) == 2

    def test_markdown_code_blocks(self):
        raw = (
            "```python\n"
            "def my_factor(df):\n"
            "    return df['close']\n"
            "```"
        )
        results = FactorParser.parse(raw)
        # Since no <function> tags, fallback def-detection should pick it up
        assert len(results) >= 1
        assert "def my_factor(df):" in results[0]
        assert "```" not in results[0]

    def test_fallback_def_detection(self):
        raw = (
            "def factor_one(df):\n"
            "    return df['open']\n"
            "\n"
            "def factor_two(df):\n"
            "    return df['close']\n"
        )
        results = FactorParser.parse(raw)
        assert len(results) == 2

    def test_normalize_indentation(self):
        raw = (
            "<function 1>\n"
            "        def my_factor(df):\n"
            "            return df['high']\n"
            "</function 1>"
        )
        results = FactorParser.parse(raw)
        assert len(results) == 1
        lines = results[0].splitlines()
        assert lines[0].startswith("def ")

    def test_empty_and_non_code_input(self):
        assert FactorParser.parse("") == []
        assert FactorParser.parse("Hello world, no code here") == []
        assert FactorParser.parse(None) == []

    def test_validate_syntax(self):
        ok, msg = FactorParser.validate_syntax("def f(x): return x")
        assert ok is True
        assert msg == ""

        ok, msg = FactorParser.validate_syntax("def f(x) return x")
        assert ok is False
        assert "SyntaxError" in msg
