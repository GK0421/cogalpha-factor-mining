import pytest
import pandas as pd
import numpy as np

from cogalpha.factors.quality import QualityChecker


class TestQualityChecker:

    @pytest.fixture
    def checker(self):
        return QualityChecker()

    @pytest.fixture
    def sample_df(self):
        return pd.DataFrame({
            "symbol": ["A", "A", "B", "B"],
            "date": pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-01", "2024-01-02"]),
            "open": [1.0, 2.0, 3.0, 4.0],
            "close": [1.1, 2.1, 3.1, 4.1],
            "high": [1.2, 2.2, 3.2, 4.2],
            "low": [0.9, 1.9, 2.9, 3.9],
        }).set_index(["date", "symbol"])

    def test_shift_negative_detected(self, checker):
        code = "def f(df): return df['close'].shift(-1)"
        result = checker.scan(code)
        assert any("shift(-N)" in w for w in result["warnings"])

    def test_shift_positive_ok(self, checker):
        code = "def f(df): return df['close'].shift(1)"
        result = checker.scan(code)
        assert not any("shift(-N)" in w for w in result["warnings"])

    def test_iloc_negative_detected(self, checker):
        code = "def f(df): return df['close'].iloc[-1]"
        result = checker.scan(code)
        assert any("iloc[-N]" in w for w in result["warnings"])

    def test_valid_code_passes(self, checker, sample_df):
        code = (
            "def my_factor(df):\n"
            "    return df['close'] / df['open']\n"
        )
        scan = checker.scan(code)
        assert scan["passed"] is True
        assert len(scan["errors"]) == 0

        sig_ok = checker.check_signature(code)
        assert sig_ok is True

        run_ok, msg = checker.check_runnable(code, sample_df)
        assert run_ok is True, msg

    def test_invalid_signature_no_args(self, checker):
        code = "def my_factor(): return 1"
        assert checker.check_signature(code) is False

    def test_invalid_signature_two_args(self, checker):
        code = "def my_factor(a, b): return a + b"
        assert checker.check_signature(code) is False

    def test_invalid_signature_no_return(self, checker):
        code = "def my_factor(df): pass"
        assert checker.check_signature(code) is False

    def test_full_check_on_bad_code(self, checker, sample_df):
        code = "def f(df): return df['close'].shift(-1)"
        result = checker.full_check(code, sample_df)
        assert result["passed"] is True  # runnable and signature OK, but warnings present
        assert any("shift(-N)" in w for w in result["warnings"])
