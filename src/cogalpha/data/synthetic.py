"""Synthetic data generation for CogAlpha MVP."""
import pandas as pd
import numpy as np
from pathlib import Path


def generate_synthetic_ohlcv(
    n_symbols: int = 3,
    n_days: int = 500,
    start_date: str = "2018-01-01",
    random_state: int = 42,
    # Backwards-compatible aliases for CLI / MVP
    symbols=None,
    end_date=None,
    freq="B",
    seed=None,
) -> pd.DataFrame:
    """Generate a multi-index DataFrame with synthetic OHLCV data."""
    # Resolve seed / random_state
    rng_seed = seed if seed is not None else random_state
    rng = np.random.default_rng(rng_seed)

    # Resolve symbols list
    if symbols is not None:
        _symbols = list(symbols)
    else:
        _symbols = [f"SYM{i}" for i in range(n_symbols)]

    # Resolve date range
    if end_date is not None:
        date_range = pd.date_range(start=start_date, end=end_date, freq=freq)
    else:
        date_range = pd.date_range(start=start_date, periods=n_days, freq=freq)

    records = []
    for sym in _symbols:
        # Random walk with drift for close prices
        drift = 0.0002
        volatility = 0.02
        returns = rng.normal(drift, volatility, len(date_range))
        prices = 100.0 * np.exp(np.cumsum(returns))

        intraday_noise = rng.uniform(0.005, 0.02, len(date_range))
        open_prices = prices * (1 + rng.normal(0, 0.005, len(date_range)))
        high_prices = np.maximum(open_prices, prices) * (1 + intraday_noise)
        low_prices = np.minimum(open_prices, prices) * (1 - intraday_noise)
        volume = rng.integers(1_000_000, 10_000_000, len(date_range))

        for i, d in enumerate(date_range):
            records.append({
                "symbol": sym,
                "date": d,
                "open": round(open_prices[i], 4),
                "high": round(high_prices[i], 4),
                "low": round(low_prices[i], 4),
                "close": round(prices[i], 4),
                "volume": int(volume[i]),
                "vwap": round((high_prices[i] + low_prices[i] + prices[i]) / 3, 4),
            })

    df = pd.DataFrame.from_records(records)
    df.set_index(["date", "symbol"], inplace=True)
    df.sort_index(inplace=True)
    return df


def save_synthetic(df: pd.DataFrame, path: str) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path)


def load_synthetic(path: str) -> pd.DataFrame:
    return pd.read_parquet(path)
