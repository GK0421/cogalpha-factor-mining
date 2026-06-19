import pytest
import pandas as pd
import numpy as np

from cogalpha.factors.leakage import LeakageDetector


def make_synthetic_panel(n_dates=20, n_symbols=5, seed=42):
    """Create a small synthetic panel DataFrame with MultiIndex (date, symbol)."""
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2024-01-01", periods=n_dates)
    symbols = [f"S{i}" for i in range(n_symbols)]

    rows = []
    for d in dates:
        for s in symbols:
            base = rng.random()
            rows.append({
                "date": d,
                "symbol": s,
                "open": base,
                "close": base + rng.random() * 0.1,
                "high": base + rng.random() * 0.2,
                "low": base - rng.random() * 0.1,
            })
    df = pd.DataFrame(rows).set_index(["date", "symbol"])
    return df


class TestLeakageDetector:

    @pytest.fixture
    def detector(self):
        return LeakageDetector()

    @pytest.fixture
    def synthetic_df(self):
        return make_synthetic_panel()

    def test_leaking_factor_caught(self, detector, synthetic_df):
        """A factor using shift(-1) on close should be flagged as leaking."""
        code = (
            "def leaky_factor(df):\n"
            "    return df['close'].shift(-1)\n"
        )
        result = detector.detect(code, synthetic_df, n_trials=5)
        assert result["suspected_leakage"] is True
        assert len(result["failed_dates"]) > 0
        assert result["max_diff"] > 1e-10

    def test_non_leaking_factor_passes(self, detector, synthetic_df):
        """A factor using shift(1) or rolling mean should not leak."""
        code = (
            "def good_factor(df):\n"
            "    return df['close'].shift(1) / df['close']\n"
        )
        result = detector.detect(code, synthetic_df, n_trials=5)
        assert result["suspected_leakage"] is False
        assert len(result["failed_dates"]) == 0

    def test_rolling_mean_passes(self, detector, synthetic_df):
        code = (
            "def rolling_factor(df):\n"
            "    return df['close'].rolling(3).mean()\n"
        )
        result = detector.detect(code, synthetic_df, n_trials=5)
        # Note: rolling mean can produce NaN at early dates, but should not leak
        assert result["suspected_leakage"] is False

    def test_comparison_robust_to_nan(self, detector, synthetic_df):
        """If the factor returns NaN at some dates, the detector should still be stable."""
        code = (
            "def nan_factor(df):\n"
            "    return df['close'].rolling(5).mean()\n"
        )
        result = detector.detect(code, synthetic_df, n_trials=5)
        # Should not crash and should not falsely flag leakage
        assert "error" not in result or result.get("error") is None
