"""LeakageDetector — empirically test for forward-looking bias in factors."""
import ast
import random

import pandas as pd
import numpy as np


class LeakageDetector:
    """Detect future-information leakage by comparing full vs truncated data results."""

    @staticmethod
    def detect(code: str, df: pd.DataFrame, n_trials: int = 5) -> dict:
        """Run factor on full data and truncated data; differing values at sampled date = leakage."""
        try:
            tree = ast.parse(code)
            func_names = [n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
            if not func_names:
                return _error("No function definition found.")
            ns = {"pd": pd, "np": np}
            exec(code, ns)
            func = ns[func_names[0]]
        except Exception as e:
            return _error(f"Failed to parse/execute code: {e}")

        df = _ensure_datetime(df)
        dates = df.index.unique().sort_values()
        n_trials = min(n_trials, len(dates))
        if n_trials == 0:
            return {"suspected_leakage": False, "trials": [], "max_diff": np.nan, "failed_dates": []}

        sampled = sorted(random.sample(list(dates), n_trials))
        trials, failed_dates, max_diff = [], [], 0.0

        for d in sampled:
            try:
                full, trunc = func(df), func(df[df.index <= d])
            except Exception as e:
                trials.append({"date": d, "error": str(e)})
                failed_dates.append(str(d))
                continue
            vf, vt = _at_date(full, d), _at_date(trunc, d)
            leaked, diff = _compare(vf, vt)
            trials.append({"date": d, "full": vf, "trunc": vt, "diff": diff})
            if leaked:
                failed_dates.append(str(d))
            max_diff = max(max_diff, diff) if not np.isnan(diff) else max_diff

        return {"suspected_leakage": bool(failed_dates), "trials": trials, "max_diff": max_diff, "failed_dates": failed_dates}

    def check(self, factor) -> bool:
        """MVP lightweight keyword scan for future-info leakage."""
        from cogalpha.factors.object import FactorObject
        if not isinstance(factor, FactorObject):
            return False
        code = factor.raw_code.lower()
        for kw in ("shift(-", "lead(", "future", "tomorrow", "next_close", "next_day"):
            if kw in code:
                factor.status = "invalid"
                factor.error_type = "future_info"
                factor.errors.append(f"Future info leakage: {kw}")
                return False
        return True


def _error(msg: str) -> dict:
    return {"suspected_leakage": True, "trials": [], "max_diff": np.nan, "failed_dates": [], "error": msg}


def _ensure_datetime(df: pd.DataFrame) -> pd.DataFrame:
    if not isinstance(df.index, pd.DatetimeIndex):
        if "date" in df.columns:
            df = df.set_index("date")
        elif isinstance(df.index, pd.MultiIndex):
            df = df.reset_index(level=1)
        df.index = pd.to_datetime(df.index)
    return df


def _at_date(result, date):
    """Extract all non-NaN values from a Series or DataFrame at a given date."""
    try:
        is_multi = isinstance(result.index, pd.MultiIndex)
        if isinstance(result, pd.Series):
            vals = result.xs(date, level=0) if is_multi else result[result.index == date]
        elif isinstance(result, pd.DataFrame):
            vals = result.xs(date, level=0) if is_multi else result[result.index == date]
        else:
            return []
        return [v for v in (vals.values.flatten() if isinstance(result, pd.DataFrame) else vals.tolist()) if not pd.isna(v)]
    except Exception:
        return []


def _compare(full, trunc) -> tuple[bool, float]:
    """Return (leaked, max_diff)."""
    if not full or not trunc:
        return bool(full) != bool(trunc), 1.0
    diff = max(abs(float(a) - float(b)) for a, b in zip(full, trunc)) if len(full) == len(trunc) else 1.0
    return diff > 1e-10, diff
