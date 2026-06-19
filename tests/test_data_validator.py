"""Tests for data validation."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from cogalpha.data.synthetic import generate_synthetic_ohlcv
from cogalpha.data.validator import DataValidator


def test_synthetic_passes_all_validations():
    df = generate_synthetic_ohlcv(n_symbols=2, n_days=100)
    validator = DataValidator(df)
    report = validator.anomaly_report()
    assert report["ohlcv"]["has_all_columns"] is True
    assert report["ohlcv"]["high_valid"] is True
    assert report["ohlcv"]["low_valid"] is True
    assert report["missing"]["open"] == 0
    assert report["missing"]["high"] == 0
    assert report["missing"]["low"] == 0
    assert report["missing"]["close"] == 0
    assert report["missing"]["volume"] == 0


def test_missing_column_detection():
    df = generate_synthetic_ohlcv(n_symbols=1, n_days=10)
    df = df.drop(columns=["volume"])
    validator = DataValidator(df)
    result = validator.validate_ohlcv()
    assert result["has_all_columns"] is False
    assert "volume" in result["missing_columns"]
    assert result["high_valid"] is None
    assert result["low_valid"] is None


def test_forward_fill():
    df = pd.DataFrame({
        "date": ["2023-01-01", "2023-01-02", "2023-01-03",
                 "2023-01-01", "2023-01-02", "2023-01-03"],
        "symbol": ["A", "A", "A", "B", "B", "B"],
        "open": [1.0, 2.0, 3.0, 1.0, 2.0, 3.0],
        "high": [1.1, 2.1, 3.1, 1.1, 2.1, 3.1],
        "low": [0.9, 1.9, 2.9, 0.9, 1.9, 2.9],
        "close": [1.0, 2.0, 3.0, float("nan"), 2.0, 3.0],
        "volume": [100, 200, 300, 100, 200, 300],
    })
    df.set_index(["date", "symbol"], inplace=True)
    validator = DataValidator(df)
    filled = validator.forward_fill()
    assert filled["close"].isna().sum() == 0
    # Row with NaN at start of group B should be dropped
    assert len(filled) == 5


def test_anomaly_report_structure():
    df = generate_synthetic_ohlcv(n_symbols=1, n_days=10)
    validator = DataValidator(df)
    report = validator.anomaly_report()
    assert "ohlcv" in report
    assert "missing" in report
    assert "total_rows" in report
    assert isinstance(report["ohlcv"], dict)
    assert isinstance(report["missing"], dict)
    assert report["total_rows"] == 10
