"""Data loading utilities."""

from __future__ import annotations

import pandas as pd


def load_data(path: str) -> pd.DataFrame:
    if path.endswith(".parquet"):
        df = pd.read_parquet(path)
    elif path.endswith(".csv"):
        df = pd.read_csv(path)
    else:
        raise ValueError(f"Unsupported file format: {path}")

    expected = {"open", "high", "low", "close", "volume"}
    if not expected.issubset(df.columns):
        df.columns = [c.lower() for c in df.columns]

    return df
