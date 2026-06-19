"""Data validation utilities."""

from __future__ import annotations

import pandas as pd


class DataValidator:
    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()

    def validate_ohlcv(self) -> dict:
        required = {"open", "high", "low", "close", "volume"}
        columns = set(self.df.columns)
        missing = list(required - columns)

        checks = {
            "missing_columns": missing,
            "has_all_columns": len(missing) == 0,
        }

        if checks["has_all_columns"]:
            high_check = (
                self.df["high"] >= self.df[["open", "close"]].max(axis=1)
            ).all()
            low_check = (
                self.df["low"] <= self.df[["open", "close"]].min(axis=1)
            ).all()
            checks["high_valid"] = bool(high_check)
            checks["low_valid"] = bool(low_check)
        else:
            checks["high_valid"] = None
            checks["low_valid"] = None

        return checks

    def validate_date_range(self, start: str, end: str) -> dict:
        if "date" not in self.df.index.names and "date" not in self.df.columns:
            return {"has_date_index": False, "within_range": None}

        if "date" in self.df.index.names:
            dates = self.df.index.get_level_values("date")
        else:
            dates = pd.to_datetime(self.df["date"])

        min_date = dates.min()
        max_date = dates.max()

        start_dt = pd.to_datetime(start)
        end_dt = pd.to_datetime(end)

        return {
            "has_date_index": True,
            "min_date": min_date,
            "max_date": max_date,
            "within_range": min_date >= start_dt and max_date <= end_dt,
        }

    def check_missing(self) -> dict:
        return self.df.isna().sum().to_dict()

    def forward_fill(self) -> pd.DataFrame:
        df = self.df.copy()
        if "symbol" in df.index.names:
            df = df.groupby(level="symbol").ffill()
        elif "symbol" in df.columns:
            df = df.groupby("symbol").ffill()
        else:
            df = df.ffill()
        return df.dropna()

    def anomaly_report(self) -> dict:
        return {
            "ohlcv": self.validate_ohlcv(),
            "missing": self.check_missing(),
            "total_rows": len(self.df),
        }
