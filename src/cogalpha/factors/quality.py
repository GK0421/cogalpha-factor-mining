"""QualityChecker — static and lightweight runtime checks for generated factors."""

import ast
import re

import pandas as pd
import numpy as np


class QualityChecker:
    """Check generated code for common anti-patterns and structural issues."""

    # Patterns that indicate future-information leakage
    LEAKAGE_PATTERNS = [
        (r'shift\s*\(\s*-\d+\s*\)', "shift(-N) uses future data"),
        (r'iloc\s*\[\s*-\d+\s*\]', "iloc[-N] uses future data"),
        (r'tail\s*\(\s*\d*\s*\)', "tail(N) can look ahead at the end of a group"),
        (r'at\s*\[\s*-1\s*,', "at[-1, ...] uses future data"),
        (r'iat\s*\[\s*-1\s*,', "iat[-1, ...] uses future data"),
        (r'\.loc\s*\[\s*[^\]]*today\s*:\s*\]', "forward-looking .loc slice"),
    ]

    def scan(self, code: str) -> dict:
        """Scan code for suspicious patterns and structural issues."""
        errors = []
        warnings = []

        for pattern, message in self.LEAKAGE_PATTERNS:
            if re.search(pattern, code):
                warnings.append(f"Future leak warning: {message}")

        # Additional structural checks via AST
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            errors.append(f"Syntax error: {e}")
            return {"passed": False, "errors": errors, "warnings": warnings}

        # Check for exactly one top-level function
        func_defs = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
        if len(func_defs) == 0:
            errors.append("No function definition found.")
        elif len(func_defs) > 1:
            warnings.append("Multiple function definitions found; only the first may be used.")

        return {"passed": len(errors) == 0, "errors": errors, "warnings": warnings}

    def check_signature(self, code: str) -> bool:
        """Verify that the code contains exactly one top-level function
        that takes exactly one positional argument.
        """
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return False

        top_level_funcs = [
            node for node in ast.iter_child_nodes(tree)
            if isinstance(node, ast.FunctionDef)
        ]

        if len(top_level_funcs) != 1:
            return False

        func = top_level_funcs[0]
        args = func.args
        # Exactly one positional argument (no defaults, no *args, no **kwargs)
        n_positional = len(args.args) + len(args.posonlyargs)
        if n_positional != 1:
            return False
        if args.vararg or args.kwarg:
            return False
        if args.kwonlyargs:
            return False
        # (Optional) function should have a return statement
        has_return = any(
            isinstance(node, ast.Return) for node in ast.walk(func)
        )
        return has_return

    def check_runnable(self, code: str, df: pd.DataFrame) -> tuple[bool, str]:
        """Execute the code in a sandboxed namespace and call the function."""
        try:
            namespace = {"pd": pd, "np": np}
            exec(code, namespace)

            # Find the function name
            tree = ast.parse(code)
            func_names = [
                node.name for node in ast.walk(tree)
                if isinstance(node, ast.FunctionDef)
            ]
            if not func_names:
                return False, "No function definition found in code."

            func = namespace[func_names[0]]
            result = func(df)

            if not isinstance(result, (pd.Series, pd.DataFrame)):
                return False, f"Function returned {type(result)}, expected pd.Series or pd.DataFrame."
            return True, ""
        except Exception as e:
            return False, f"Runtime error: {e}"

    def full_check(self, code: str, df: pd.DataFrame) -> dict:
        """Run all checks and return a unified report."""
        scan_result = self.scan(code)
        sig_ok = self.check_signature(code)
        run_ok, run_msg = self.check_runnable(code, df)

        errors = list(scan_result["errors"])
        warnings = list(scan_result["warnings"])

        if not sig_ok:
            errors.append("Invalid function signature: must be exactly one top-level function with one argument.")
        if not run_ok:
            errors.append(run_msg)

        return {
            "passed": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
        }

    def check(self, factor) -> bool:
        """MVP helper: check a FactorObject and update its status."""
        # We need a DataFrame to run full_check; for MVP we do a lightweight check
        from cogalpha.factors.object import FactorObject
        if not isinstance(factor, FactorObject):
            return False
        code = factor.raw_code
        scan = self.scan(code)
        sig_ok = self.check_signature(code)
        if not scan["passed"] or not sig_ok:
            factor.status = "invalid"
            factor.error_type = "syntax" if any("Syntax" in e for e in scan["errors"]) else "logic"
            factor.errors = scan["errors"] + (["Invalid signature"] if not sig_ok else [])
            return False
        factor.status = "valid"
        factor.error_type = None
        return True
