"""FactorEvaluator — compute predictive metrics for a factor against forward returns."""

import numpy as np
import pandas as pd
import scipy.stats


class FactorEvaluator:
    """Evaluate a factor's cross-sectional predictive power."""

    def __init__(
        self,
        df: pd.DataFrame,
        train_start: str,
        train_end: str,
        test_start: str,
        test_end: str,
    ):
        self.df = df.copy()
        self.train_start = pd.to_datetime(train_start)
        self.train_end = pd.to_datetime(train_end)
        self.test_start = pd.to_datetime(test_start)
        self.test_end = pd.to_datetime(test_end)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def compute_forward_return(df: pd.DataFrame, periods: int = 1) -> pd.Series:
        """
        Compute close.shift(-periods) / close - 1 grouped by symbol.
        This is the prediction target, not the factor itself.
        """
        if "symbol" not in df.columns and not isinstance(df.index, pd.MultiIndex):
            raise ValueError("DataFrame must contain a 'symbol' column or MultiIndex with symbol level.")

        # Work with a MultiIndex (date, symbol) for uniform grouping
        if isinstance(df.index, pd.MultiIndex):
            temp = df.copy()
        else:
            temp = df.set_index("symbol", append=True).swaplevel(0, 1)

        # Compute forward return per symbol
        fwd = temp.groupby(level=1)["close"].shift(-periods) / temp["close"] - 1
        return fwd

    def _slice(self, split: str) -> pd.DataFrame:
        """Return train or test slice of the DataFrame."""
        if split == "train":
            mask = (self.df.index.get_level_values(0) >= self.train_start) & \
                   (self.df.index.get_level_values(0) <= self.train_end)
            # If simple index, try column-based date
            if not mask.any() and "date" in self.df.columns:
                mask = (self.df["date"] >= self.train_start) & (self.df["date"] <= self.train_end)
            return self.df[mask]
        elif split == "test":
            mask = (self.df.index.get_level_values(0) >= self.test_start) & \
                   (self.df.index.get_level_values(0) <= self.test_end)
            if not mask.any() and "date" in self.df.columns:
                mask = (self.df["date"] >= self.test_start) & (self.df["date"] <= self.test_end)
            return self.df[mask]
        else:
            raise ValueError(f"split must be 'train' or 'test', got {split}")

    # ------------------------------------------------------------------
    # Evaluation
    # ------------------------------------------------------------------
    def evaluate(
        self,
        factor_values: pd.Series,
        period: int = 1,
        split: str = "train",
    ) -> dict:
        """
        Evaluate a factor on a given split.

        Parameters
        ----------
        factor_values : pd.Series
            Series with same index as self.df (or aligned after reset).
        period : int
            Forward-return horizon.
        split : str
            "train" or "test".
        """
        df_slice = self._slice(split)

        # Align factor_values to the slice
        # factor_values should have the same index as self.df
        aligned_factor = factor_values.loc[factor_values.index.intersection(df_slice.index)]

        # Compute forward returns on the FULL data, then align to the slice
        fwd_returns = self.compute_forward_return(self.df, periods=period)
        aligned_fwd = fwd_returns.loc[fwd_returns.index.intersection(df_slice.index)]

        # Drop NaNs jointly
        valid = aligned_factor.notna() & aligned_fwd.notna()
        f = aligned_factor[valid]
        r = aligned_fwd[valid]

        if len(f) == 0:
            return {
                "split": split,
                "period": period,
                "sample_size": 0,
                "ic": np.nan,
                "rankic": np.nan,
                "icir": np.nan,
                "rankicir": np.nan,
                "long_short_return": np.nan,
                "quantile_returns": {},
            }

        # --- IC and RankIC per day (cross-sectional) ---
        if isinstance(f.index, pd.MultiIndex):
            dates = f.index.get_level_values(0).unique()
            ic_list = []
            ric_list = []
            for d in dates:
                f_day = f.xs(d, level=0)
                r_day = r.xs(d, level=0)
                valid_day = f_day.notna() & r_day.notna()
                f_day = f_day[valid_day]
                r_day = r_day[valid_day]
                if len(f_day) < 2:
                    continue
                ic = np.corrcoef(f_day, r_day)[0, 1]
                ric, _ = scipy.stats.spearmanr(f_day, r_day)
                if not np.isnan(ic):
                    ic_list.append(ic)
                if not np.isnan(ric):
                    ric_list.append(ric)
        else:
            # Panel evaluation (single time series)
            ic_list = [np.corrcoef(f, r)[0, 1]]
            ric_list = [scipy.stats.spearmanr(f, r)[0]]

        ic_arr = np.array(ic_list)
        ric_arr = np.array(ric_list)

        ic_mean = np.nanmean(ic_arr) if len(ic_arr) > 0 else np.nan
        ric_mean = np.nanmean(ric_arr) if len(ric_arr) > 0 else np.nan
        ic_std = np.nanstd(ic_arr) if len(ic_arr) > 0 else np.nan
        ric_std = np.nanstd(ric_arr) if len(ric_arr) > 0 else np.nan

        icir = ic_mean / ic_std if ic_std != 0 and not np.isnan(ic_std) else np.nan
        rankicir = ric_mean / ric_std if ric_std != 0 and not np.isnan(ric_std) else np.nan

        # --- Group / quantile returns ---
        if isinstance(f.index, pd.MultiIndex):
            dates = f.index.get_level_values(0).unique()
            quantile_returns = {q: [] for q in range(1, 6)}
            long_short = []
            for d in dates:
                f_day = f.xs(d, level=0)
                r_day = r.xs(d, level=0)
                valid_day = f_day.notna() & r_day.notna()
                f_day = f_day[valid_day]
                r_day = r_day[valid_day]
                if len(f_day) < 5:
                    continue
                # 5 quantiles
                labels = pd.qcut(f_day, 5, labels=False, duplicates="drop")
                if labels.isna().all():
                    continue
                day_ret = r_day.groupby(labels).mean()
                for q in range(5):
                    if q in day_ret.index:
                        quantile_returns[q + 1].append(day_ret[q])
                if 0 in day_ret.index and 4 in day_ret.index:
                    long_short.append(day_ret[4] - day_ret[0])
            avg_quantile = {q: np.nanmean(v) if v else np.nan for q, v in quantile_returns.items()}
            long_short_return = np.nanmean(long_short) if long_short else np.nan
        else:
            labels = pd.qcut(f, 5, labels=False, duplicates="drop")
            day_ret = r.groupby(labels).mean()
            avg_quantile = {q + 1: (day_ret[q] if q in day_ret.index else np.nan) for q in range(5)}
            long_short_return = (
                day_ret[4] - day_ret[0] if 4 in day_ret.index and 0 in day_ret.index else np.nan
            )

        return {
            "split": split,
            "period": period,
            "sample_size": int(len(f)),
            "ic": round(ic_mean, 6),
            "rankic": round(ric_mean, 6),
            "icir": round(icir, 6),
            "rankicir": round(rankicir, 6),
            "long_short_return": round(long_short_return, 6),
            "quantile_returns": {k: round(v, 6) if not np.isnan(v) else None for k, v in avg_quantile.items()},
        }

    def evaluate_factor(self, factor) -> dict:
        """MVP helper: evaluate a FactorObject by executing its code on the stored df."""
        import ast
        from cogalpha.factors.object import FactorObject
        if not isinstance(factor, FactorObject):
            raise TypeError("factor must be a FactorObject")
        code = factor.raw_code
        namespace = {"pd": pd, "np": np}
        try:
            exec(code, namespace)
            tree = ast.parse(code)
            func_names = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
            if not func_names:
                raise ValueError("No function found in factor code")
            func = namespace[func_names[0]]
            factor_values = func(self.df)
            metrics = self.evaluate(factor_values, period=1, split="train")
            factor.metrics = metrics
            return metrics
        except Exception as e:
            factor.errors.append(f"evaluation_error: {type(e).__name__}: {e}")
            factor.status = "invalid"
            return {}

    def evaluate_all(self, factors: list[pd.Series]) -> list[dict]:
        """Evaluate a list of factors and return metrics for each."""
        return [self.evaluate(f) for f in factors]
