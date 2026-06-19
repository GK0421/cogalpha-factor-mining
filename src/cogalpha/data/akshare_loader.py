"""AKShare A-share daily OHLCV data loader.

AKShare is a free, open-source financial data interface library for Chinese markets.
This module fetches real A-share daily OHLCV data and returns a standardized DataFrame.

Usage:
    from cogalpha.data.akshare_loader import fetch_ashare_daily
    df = fetch_ashare_daily(start_date="20220101", end_date="20231231")
    df.to_parquet("./data/ashare_daily.parquet")
"""

import os
from datetime import datetime, timedelta
from typing import Optional

import pandas as pd

from ..config import Config, load_config


def _ensure_akshare():
    """Lazy import akshare with helpful error message."""
    try:
        import akshare as ak  # noqa: F401
        return ak
    except ImportError:
        raise ImportError(
            "akshare is required for real market data. "
            "Install it with: pip install akshare"
        )


def fetch_ashare_daily(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    symbols: Optional[list[str]] = None,
    adj: str = "qfq",  # "qfq" = 前复权, "hfq" = 后复权, "" = 不复权
) -> pd.DataFrame:
    """Fetch A-share daily OHLCV data via AKShare.

    Args:
        start_date: YYYYMMDD format. Defaults to 1 year ago.
        end_date: YYYYMMDD format. Defaults to today.
        symbols: List of stock codes like ["000001", "000002"].
            If None, fetches all A-share stocks (slow).
        adj: Adjustment type. "qfq" (pre-adjusted) is recommended.

    Returns:
        DataFrame with MultiIndex (date, symbol) and columns:
        open, high, low, close, volume
    """
    ak = _ensure_akshare()

    if end_date is None:
        end_date = datetime.now().strftime("%Y%m%d")
    if start_date is None:
        start_date = (datetime.now() - timedelta(days=365)).strftime("%Y%m%d")

    # Validate date format
    for d in [start_date, end_date]:
        if len(d) != 8 or not d.isdigit():
            raise ValueError(f"Date must be YYYYMMDD format, got {d}")

    all_frames = []

    if symbols is None:
        # Fetch all A-share stock codes
        stock_df = ak.stock_zh_a_spot_em()
        symbols = stock_df["代码"].tolist()
        print(f"Fetching all {len(symbols)} A-share stocks... This may take a while.")

    for code in symbols:
        try:
            # Fetch historical data for a single stock
            # akshare returns columns: 日期, 开盘, 收盘, 最高, 最低, 成交量
            df = ak.stock_zh_a_hist(
                symbol=code,
                period="daily",
                start_date=start_date,
                end_date=end_date,
                adjust=adj,
            )
            if df is None or df.empty:
                continue

            # Standardize column names
            df = df.rename(
                columns={
                    "日期": "date",
                    "开盘": "open",
                    "收盘": "close",
                    "最高": "high",
                    "最低": "low",
                    "成交量": "volume",
                }
            )
            df["symbol"] = code
            df["date"] = pd.to_datetime(df["date"])

            # Keep only required columns
            cols = ["date", "symbol", "open", "high", "low", "close", "volume"]
            df = df[[c for c in cols if c in df.columns]]

            all_frames.append(df)
        except Exception as e:
            # Log but continue — some stocks may fail
            print(f"  [SKIP] {code}: {e}")
            continue

    if not all_frames:
        raise RuntimeError("No data fetched. Check date range and symbols.")

    combined = pd.concat(all_frames, ignore_index=True)
    combined = combined.set_index(["date", "symbol"]).sort_index()
    return combined


def fetch_sample_data(n_symbols: int = 5, days: int = 252) -> pd.DataFrame:
    """Fetch a small sample of real A-share data for quick testing.

    Returns:
        DataFrame with MultiIndex (date, symbol)
    """
    ak = _ensure_akshare()
    stock_df = ak.stock_zh_a_spot_em()
    # Pick top N by market cap for liquidity
    symbols = stock_df["代码"].head(n_symbols).tolist()

    end_date = datetime.now().strftime("%Y%m%d")
    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y%m%d")

    return fetch_ashare_daily(
        start_date=start_date,
        end_date=end_date,
        symbols=symbols,
        adj="qfq",
    )


def save_to_parquet(df: pd.DataFrame, path: str) -> None:
    """Save DataFrame to Parquet with appropriate settings."""
    df.to_parquet(path, engine="pyarrow", compression="zstd")
    print(f"Saved {len(df)} rows to {path}")


def load_from_parquet(path: str) -> pd.DataFrame:
    """Load DataFrame from Parquet."""
    return pd.read_parquet(path)
