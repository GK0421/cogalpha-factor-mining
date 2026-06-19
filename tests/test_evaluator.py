import pytest
import pandas as pd
import numpy as np

from cogalpha.factors.evaluator import FactorEvaluator


def make_test_panel(n_dates=30, n_symbols=4, seed=7):
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2024-01-01", periods=n_dates)
    symbols = [f"S{i}" for i in range(n_symbols)]

    rows = []
    for d in dates:
        for s in symbols:
            base = rng.random() + 1.0
            rows.append({
                "date": d,
                "symbol": s,
                "open": base,
                "close": base + rng.random() * 0.05 - 0.025,
                "high": base + rng.random() * 0.1,
                "low": base - rng.random() * 0.1,
            })
    df = pd.DataFrame(rows).set_index(["date", "symbol"])
    return df


class TestFactorEvaluator:

    @pytest.fixture
    def df(self):
        return make_test_panel()

    @pytest.fixture
    def evaluator(self, df):
        return FactorEvaluator(
            df=df,
            train_start="2024-01-01",
            train_end="2024-01-15",
            test_start="2024-01-16",
            test_end="2024-01-30",
        )

    def test_compute_forward_return(self, df):
        fwd = FactorEvaluator.compute_forward_return(df, periods=1)
        assert isinstance(fwd, pd.Series)
        # Forward return should be NaN at the last date per symbol
        for s in df.index.get_level_values(1).unique():
            last_date = df.xs(s, level=1).index[-1]
            assert pd.isna(fwd.loc[(last_date, s)])

    def test_ic_and_rankic_known_factor(self, df, evaluator):
        # Simple factor: close / open — should have some correlation with forward return
        factor = df["close"] / df["open"]
        result = evaluator.evaluate(factor, period=1, split="train")
        assert "ic" in result
        assert "rankic" in result
        assert "icir" in result
        assert "rankicir" in result
        assert not np.isnan(result["ic"])
        assert not np.isnan(result["rankic"])

    def test_train_test_split(self, df, evaluator):
        factor = df["close"] / df["open"]
        train_result = evaluator.evaluate(factor, period=1, split="train")
        test_result = evaluator.evaluate(factor, period=1, split="test")
        assert train_result["split"] == "train"
        assert test_result["split"] == "test"
        assert train_result["sample_size"] > 0
        assert test_result["sample_size"] > 0

    def test_group_returns_and_long_short(self, df, evaluator):
        factor = df["close"] / df["open"]
        result = evaluator.evaluate(factor, period=1, split="train")
        assert "long_short_return" in result
        assert "quantile_returns" in result
        assert len(result["quantile_returns"]) == 5
        # Q5 should generally be >= Q1 for a decent factor, but we just assert keys
        for q in range(1, 6):
            assert q in result["quantile_returns"]

    def test_evaluate_all(self, df, evaluator):
        factor1 = df["close"] / df["open"]
        factor2 = df["high"] / df["low"]
        results = evaluator.evaluate_all([factor1, factor2])
        assert len(results) == 2
        for r in results:
            assert "ic" in r
