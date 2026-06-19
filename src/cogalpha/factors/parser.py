"""FactorParser extracts raw code from LLM responses."""

import re
import ast


class FactorParser:
    """Parse LLM responses to extract Python code snippets."""

    @staticmethod
    def parse(raw_response: str) -> list[str]:
        """Extract code blocks from raw LLM response."""
        if not raw_response or not isinstance(raw_response, str):
            return []

        # Primary: extract <function ...> tags
        pattern = r'<function\s*\d+>(.*?)</function\s*\d+>'
        matches = re.findall(pattern, raw_response, flags=re.DOTALL)

        # If no <function> tags found, try fallback: detect top-level def blocks
        if not matches:
            fallback_pattern = r'def\s+\w+\s*\([^)]*\):(?:\n|.)*?(?=\n\s*def|\Z)'
            matches = re.findall(fallback_pattern, raw_response, flags=re.DOTALL)

        # Clean up each extracted block
        results = []
        for code in matches:
            cleaned = FactorParser._clean(code)
            if cleaned.strip():
                results.append(cleaned)
        return results

    @staticmethod
    def _clean(code: str) -> str:
        """Remove markdown fences and normalize indentation."""
        # Strip outer whitespace first
        code = code.strip()

        # Remove markdown code block markers (```python, ```, etc.)
        # Remove starting fences
        code = re.sub(r'^\s*```(?:python)?\s*\n?', '', code, flags=re.MULTILINE)
        # Remove ending fences
        code = re.sub(r'\n?\s*```\s*$', '', code, flags=re.MULTILINE)

        # Normalize indentation to 4 spaces standard
        lines = code.splitlines()
        if not lines:
            return ""

        # Find minimum common indentation (excluding empty lines)
        non_empty = [l for l in lines if l.strip()]
        if not non_empty:
            return ""

        min_indent = min(len(l) - len(l.lstrip()) for l in non_empty)
        if min_indent > 0:
            lines = [l[min_indent:] if l.strip() else l for l in lines]

        return "\n".join(lines)

    @staticmethod
    def validate_syntax(code: str) -> tuple[bool, str]:
        """Validate that the extracted code is syntactically valid Python."""
        try:
            ast.parse(code)
            return True, ""
        except SyntaxError as e:
            return False, f"SyntaxError: {e}"
        except Exception as e:
            return False, f"Unexpected error: {e}"

    @staticmethod
    def parse_to_objects(raw_response: str, agent_id: str = "mock", mode: str = "moderate") -> list:
        """Parse raw response into a list of FactorObject instances."""
        from cogalpha.factors.object import FactorObject
        import uuid
        codes = FactorParser.parse(raw_response)
        objects = []
        for i, code in enumerate(codes):
            fid = f"{agent_id}_{uuid.uuid4().hex[:8]}"
            objects.append(
                FactorObject(
                    factor_id=fid,
                    agent_id=agent_id,
                    mode=mode,
                    raw_response=raw_response,
                    raw_code=code,
                )
            )
        return objects
