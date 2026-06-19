"""LeakageDetector — empirically test for forward-looking bias in factors."""

import ast
import random

import pandas as pd
import numpy as np


class LeakageDetector:
    """Detect future-information leakage by comparing full vs truncated data results."""

    @staticmethod
    def detect(code: str, df: pd.DataFrame, n_trials: int = 5) -> dict:
        """
        Run the factor on full data and on truncated data up to each sampled date.
        If the values differ at the sampled date, the factor is using future data.
        """
        # Parse and execute to get the function object
        try:
            tree = ast.parse(code)
            func_names = [
                node.name for node in ast.walk(tree)
                if isinstance(node, ast.FunctionDef)
            ]
            if not func_names:
                return {
                    "suspected_leakage": True,
                    "trials": [],
                    "max_diff": np.nan,
                    "failed_dates": [],
                    "error": "No function definition found.",
                }

            namespace = {"pd": pd, "np": np}
            exec(code, namespace)
            func = namespace[func_names[0]]
        except Exception as e:
            return {
                "suspected_leakage": True,
                "trials": [],
                "max_diff": np.nan,
                "failed_dates": [],
                "error": f"Failed to parse/execute code: {e}",
            }

        # Ensure DataFrame has a DatetimeIndex
        if not isinstance(df.index, pd.DatetimeIndex):
            # Try to infer from a 'date' column or MultiIndex level
            if "date" in df.columns:
                df = df.set_index("date")
            elif isinstance(df.index, pd.MultiIndex):
                # Assume level 0 is date, level 1 is symbol
                df = df.reset_index(level=1)
            df.index = pd.to_datetime(df.index)

        unique_dates = df.index.unique().sort_values()
        if len(unique_dates) < n_trials:
            n_trials = len(unique_dates)
        if n_trials == 0:
            return {
                "suspected_leakage": False,
                "trials": [],
                "max_diff": np.nan,
                "failed_dates": [],
            }

        sampled_dates = random.sample(list(unique_dates), n_trials)
        sampled_dates = sorted(sampled_dates)

        trials = []
        failed_dates = []
        max_diff = 0.0

        for date in sampled_dates:
            try:
                result_full = func(df)
                # Truncate to dates <= date (inclusive)
                df_trunc = df[df.index <= date]
                result_trunc = func(df_trunc)
            except Exception as e:
                trials.append({"date": date, "error": str(e)})
                failed_dates.append(str(date))
                continue

            # Extract all values at the sampled date (handles MultiIndex)
            vals_full = _extract_at_date(result_full, date)
            vals_trunc = _extract_at_date(result_trunc, date)

            # Compare all values at this date
            date_failed = False
            date_max_diff = 0.0
            if not vals_full or not vals_trunc:
                # If one side has no values and the other does, treat as leakage
                if bool(vals_full) != bool(vals_trunc):
                    date_failed = True
                    date_max_diff = 1.0
            elif len(vals_full) != len(vals_trunc):
                date_failed = True
                # Compute diff on common prefix
                common_len = min(len(vals_full), len(vals_trunc))
                for i in range(common_len):
                    diff = _safe_diff(vals_full[i], vals_trunc[i])
                    if not np.isnan(diff) and diff > date_max_diff:
                        date_max_diff = diff
                # If no difference in common prefix but lengths differ, set a positive diff
                if date_max_diff <= 1e-10:
                    date_max_diff = 1.0
            else:
                for vf, vt in zip(vals_full, vals_trunc):
                    diff = _safe_diff(vf, vt)
                    if not np.isnan(diff) and diff > 1e-10:
                        date_failed = True
                    if not np.isnan(diff) and diff > date_max_diff:
                        date_max_diff = diff

            trials.append({
                "date": date,
                "full": vals_full,
                "trunc": vals_trunc,
                "diff": date_max_diff,
            })

            if date_failed:
                failed_dates.append(str(date))

            if not np.isnan(date_max_diff) and date_max_diff > max_diff:
                max_diff = date_max_diff

        suspected = len(failed_dates) > 0

        return {
            "suspected_leakage": suspected,
            "trials": trials,
            "max_diff": max_diff,
            "failed_dates": failed_dates,
        }

    def check(self, factor) -> bool:
        """MVP helper: check a FactorObject for leakage and update its status."""
        from cogalpha.factors.object import FactorObject
        if not isinstance(factor, FactorObject):
            return False
        # Lightweight keyword scan for MVP (full detect requires DataFrame)
        code = factor.raw_code.lower()
        future_keywords = ["shift(-", "lead(", "future", "tomorrow", "next_close", "next_day"]
        for kw in future_keywords:
            if kw in code:
                factor.status = "invalid"
                factor.error_type = "future_info"
                factor.errors.append(f"Future info leakage detected: {kw}")
                return False
        return True


def _extract_at_date(result, date):
    """Extract all values from a Series or DataFrame at a given date."""
    try:
        if isinstance(result, pd.Series):
            if isinstance(result.index, pd.MultiIndex):
                vals = result.xs(date, level=0)
                return vals.dropna().tolist() if len(vals) > 0 else []
            else:
                mask = result.index == date
                return result[mask].dropna().tolist() if mask.any() else []
        elif isinstance(result, pd.DataFrame):
            if isinstance(result.index, pd.MultiIndex):
                vals = result.xs(date, level=0)
                # Flatten to list of scalars
                flat = vals.values.flatten()
                return [v for v in flat if not pd.isna(v)] if len(vals) > 0 else []
            else:
                mask = result.index == date
                if mask.any():
                    flat = result[mask].values.flatten()
                    return [v for v in flat if not pd.isna(v)]
                return []
        else:
            return []
    except Exception:
        return []


def _safe_diff(a, b):
    """Compute absolute difference robust to NaN."""
    if pd.isna(a) and pd.isna(b):
        return 0.0
    if pd.isna(a) or pd.isna(b):
        return np.nan
    return abs(float(a) - float(b))
