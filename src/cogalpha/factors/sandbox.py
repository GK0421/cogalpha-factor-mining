"""sandbox.py — execute generated factor code in a restricted namespace."""

import ast

import pandas as pd
import numpy as np
import scipy


def sandbox_exec(code: str, df: pd.DataFrame) -> pd.Series:
    """
    Execute code in a restricted namespace and call the extracted function.

    Parameters
    ----------
    code : str
        Python code containing a function definition.
    df : pd.DataFrame
        DataFrame to pass as the single argument.

    Returns
    -------
    pd.Series
        The result of the function call.

    Raises
    ------
    ValueError
        If no function is found or execution fails.
    """
    # Parse to find the first function name
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        raise ValueError(f"Syntax error in generated code: {e}")

    func_names = [
        node.name for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef)
    ]
    if not func_names:
        raise ValueError("No function definition found in code.")

    # Restricted namespace
    namespace = {
        "pd": pd,
        "np": np,
        "scipy": scipy,
    }

    try:
        exec(code, namespace)
    except Exception as e:
        raise ValueError(f"Error executing factor code: {e}")

    func = namespace[func_names[0]]
    try:
        result = func(df)
    except Exception as e:
        raise ValueError(f"Error calling factor function: {e}")

    return result
