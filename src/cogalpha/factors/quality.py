"""QualityChecker — static and lightweight runtime checks for generated factors."""
import ast
import re

import pandas as pd
import numpy as np


class QualityChecker:
    """Check generated code for common anti-patterns and structural issues."""

    LEAKAGE_PATTERNS = [
        (r'shift\s*\(\s*-\d+\s*\)', "shift(-N) uses future data"),
        (r'iloc\s*\[\s*-\d+\s*\]', "iloc[-N] uses future data"),
        (r'tail\s*\(\s*\d*\s*\)', "tail(N) can look ahead"),
        (r'at\s*\[\s*-1\s*,', "at[-1, ...] uses future data"),
        (r'iat\s*\[\s*-1\s*,', "iat[-1, ...] uses future data"),
        (r'\.loc\s*\[\s*[^\]]*today\s*:\s*\]', "forward-looking .loc slice"),
    ]

    def _ast(self, code: str) -> ast.AST | None:
        try:
            return ast.parse(code)
        except SyntaxError as e:
            return e  # type: ignore

    def scan(self, code: str) -> dict:
        """Scan code for suspicious patterns and structural issues."""
        tree = self._ast(code)
        if isinstance(tree, SyntaxError):
            return {"passed": False, "errors": [f"Syntax error: {tree}"], "warnings": []}
        funcs = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
        errors = ["No function definition found."] if not funcs else []
        warnings = [f"Future leak: {msg}" for pat, msg in self.LEAKAGE_PATTERNS if re.search(pat, code)]
        if len(funcs) > 1:
            warnings.append("Multiple function definitions; only the first may be used.")
        return {"passed": len(errors) == 0, "errors": errors, "warnings": warnings}

    def check_signature(self, code: str) -> bool:
        """Verify exactly one top-level function with one positional arg and a return."""
        tree = self._ast(code)
        if isinstance(tree, SyntaxError):
            return False
        funcs = [n for n in ast.iter_child_nodes(tree) if isinstance(n, ast.FunctionDef)]
        if len(funcs) != 1:
            return False
        a = funcs[0].args
        return (len(a.args) + len(a.posonlyargs) == 1 and not a.vararg and not a.kwarg
                and not a.kwonlyargs and any(isinstance(n, ast.Return) for n in ast.walk(funcs[0])))

    def check_runnable(self, code: str, df: pd.DataFrame) -> tuple[bool, str]:
        """Execute code in sandboxed namespace and call the function."""
        try:
            ns = {"pd": pd, "np": np}
            exec(code, ns)
            func = ns[next(n for n, o in ns.items() if callable(o) and n not in ("pd", "np"))]
            result = func(df)
            return isinstance(result, (pd.Series, pd.DataFrame)), (
                "" if isinstance(result, (pd.Series, pd.DataFrame)) else f"Expected Series/DataFrame, got {type(result)}"
            )
        except Exception as e:
            return False, f"Runtime error: {e}"

    def full_check(self, code: str, df: pd.DataFrame) -> dict:
        scan = self.scan(code)
        run_ok, run_msg = self.check_runnable(code, df)
        errors = list(scan["errors"]) + (["Invalid signature"] if not self.check_signature(code) else [])
        if not run_ok:
            errors.append(run_msg)
        return {"passed": len(errors) == 0, "errors": errors, "warnings": scan["warnings"]}

    def check(self, factor) -> bool:
        """MVP lightweight check on a FactorObject."""
        from cogalpha.factors.object import FactorObject
        if not isinstance(factor, FactorObject):
            return False
        s = self.scan(factor.raw_code)
        sig = self.check_signature(factor.raw_code)
        ok = s["passed"] and sig
        factor.status = "valid" if ok else "invalid"
        factor.error_type = None if ok else ("syntax" if any("Syntax" in e for e in s["errors"]) else "logic")
        factor.errors = ([] if ok else s["errors"] + (["Invalid signature"] if not sig else []))
        return ok
