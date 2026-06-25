"""FactorEvaluator — compute predictive metrics for a factor against forward returns."""

import numpy as np
import pandas as pd
import scipy.stats
from typing import Callable


class FactorEvaluator:
    """Evaluate a factor's cross-sectional predictive power."""

    def __init__(self, df: pd.DataFrame, train_start: str, train_end: str, test_start: str, test_end: str):
        self.df = df.copy()
        self._dates = {
            "train": (pd.to_datetime(train_start), pd.to_datetime(train_end)),
            "test": (pd.to_datetime(test_start), pd.to_datetime(test_end)),
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def compute_forward_return(df: pd.DataFrame, periods: int = 1) -> pd.Series:
        """Compute close.shift(-periods) / close - 1 grouped by symbol."""
        if "symbol" not in df.columns and not isinstance(df.index, pd.MultiIndex):
            raise ValueError("DataFrame needs 'symbol' column or MultiIndex.")
        temp = df if isinstance(df.index, pd.MultiIndex) else df.set_index("symbol", append=True).swaplevel(0, 1)
        return temp.groupby(level=1)["close"].shift(-periods) / temp["close"] - 1

    def _slice(self, split: str) -> pd.DataFrame:
        start, end = self._dates[split]
        idx = self.df.index.get_level_values(0)
        mask = (idx >= start) & (idx <= end)
        if not mask.any() and "date" in self.df.columns:
            mask = (self.df["date"] >= start) & (self.df["date"] <= end)
        return self.df[mask]

    @staticmethod
    def _is_multi(f: pd.Series) -> bool:
        return isinstance(f.index, pd.MultiIndex)

    @staticmethod
    def _per_day(f: pd.Series, r: pd.Series, fn: Callable[[pd.Series, pd.Series], tuple]) -> list:
        """Apply fn(f_day, r_day) per day; return list of results."""
        if not FactorEvaluator._is_multi(f):
            return [fn(f, r)]
        out = []
        for d in f.index.get_level_values(0).unique():
            fd, rd = f.xs(d, level=0), r.xs(d, level=0)
            valid = fd.notna() & rd.notna()
            fd, rd = fd[valid], rd[valid]
            if len(fd) >= 2:
                out.append(fn(fd, rd))
        return out

    # ------------------------------------------------------------------
    # Evaluation
    # ------------------------------------------------------------------
    def evaluate(self, factor_values: pd.Series, period: int = 1, split: str = "train") -> dict:
        df_slice = self._slice(split)
        f = factor_values.loc[factor_values.index.intersection(df_slice.index)]
        fwd = self.compute_forward_return(self.df, periods=period)
        r = fwd.loc[fwd.index.intersection(df_slice.index)]
        valid = f.notna() & r.notna()
        f, r = f[valid], r[valid]

        if len(f) == 0:
            return self._empty_result(split, period)

        # IC / RankIC per day
        ic_vals = self._per_day(f, r, lambda fd, rd: (np.corrcoef(fd, rd)[0, 1], scipy.stats.spearmanr(fd, rd)[0]))
        ic_arr = np.array([v[0] for v in ic_vals if not np.isnan(v[0])])
        ric_arr = np.array([v[1] for v in ic_vals if not np.isnan(v[1])])

        ic_mean, ric_mean = np.nanmean(ic_arr) if len(ic_arr) else np.nan, np.nanmean(ric_arr) if len(ric_arr) else np.nan
        ic_std, ric_std = np.nanstd(ic_arr) if len(ic_arr) else np.nan, np.nanstd(ric_arr) if len(ric_arr) else np.nan
        icir = ic_mean / ic_std if ic_std and not np.isnan(ic_std) else np.nan
        rankicir = ric_mean / ric_std if ric_std and not np.isnan(ric_std) else np.nan

        # Quantile returns
        q_ret, ls = self._quantile_returns(f, r)

        return {
            "split": split,
            "period": period,
            "sample_size": int(len(f)),
            "ic": round(ic_mean, 6),
            "rankic": round(ric_mean, 6),
            "icir": round(icir, 6),
            "rankicir": round(rankicir, 6),
            "long_short_return": round(ls, 6) if not np.isnan(ls) else None,
            "quantile_returns": {k: round(v, 6) if not np.isnan(v) else None for k, v in q_ret.items()},
        }

    def _quantile_returns(self, f: pd.Series, r: pd.Series) -> tuple[dict, float]:
        """Return (avg_quantile_returns, long_short_return)."""
        if not self._is_multi(f):
            labels = pd.qcut(f, 5, labels=False, duplicates="drop")
            day_ret = r.groupby(labels).mean()
            q = {q + 1: (day_ret[q] if q in day_ret.index else np.nan) for q in range(5)}
            ls = day_ret[4] - day_ret[0] if 4 in day_ret.index and 0 in day_ret.index else np.nan
            return q, ls

        q_vals = {q: [] for q in range(1, 6)}
        ls_vals = []
        for d in f.index.get_level_values(0).unique():
            fd, rd = f.xs(d, level=0), r.xs(d, level=0)
            valid = fd.notna() & rd.notna()
            fd, rd = fd[valid], rd[valid]
            if len(fd) < 5:
                continue
            labels = pd.qcut(fd, 5, labels=False, duplicates="drop")
            if labels.isna().all():
                continue
            day_ret = rd.groupby(labels).mean()
            for q in range(5):
                if q in day_ret.index:
                    q_vals[q + 1].append(day_ret[q])
            if 0 in day_ret.index and 4 in day_ret.index:
                ls_vals.append(day_ret[4] - day_ret[0])
        return {q: np.nanmean(v) if v else np.nan for q, v in q_vals.items()}, np.nanmean(ls_vals) if ls_vals else np.nan

    @staticmethod
    def _empty_result(split: str, period: int) -> dict:
        return {"split": split, "period": period, "sample_size": 0, "ic": np.nan, "rankic": np.nan,
                "icir": np.nan, "rankicir": np.nan, "long_short_return": np.nan, "quantile_returns": {}}

    def evaluate_factor(self, factor) -> dict:
        """MVP helper: evaluate a FactorObject by executing its code on the stored df."""
        import ast
        from cogalpha.factors.object import FactorObject
        if not isinstance(factor, FactorObject):
            raise TypeError("factor must be a FactorObject")
        try:
            ns = {"pd": pd, "np": np}
            exec(factor.raw_code, ns)
            func = ns[next(n for n, o in ns.items() if callable(o) and n not in ("pd", "np"))]
            factor.metrics = self.evaluate(func(self.df), period=1, split="train")
            return factor.metrics
        except Exception as e:
            factor.errors.append(f"evaluation_error: {type(e).__name__}: {e}")
            factor.status = "invalid"
            return {}

    def evaluate_all(self, factors: list[pd.Series]) -> list[dict]:
        return [self.evaluate(f) for f in factors]
