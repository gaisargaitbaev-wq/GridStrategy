"""
Optional sample data generator (standalone utility).
This script is provided as a convenience to create synthetic OHLCV CSVs for quick testing.

It is not used by the main quick-start flow (the backtester requires a real data CSV supplied via
`config/default_config.json:data_path` or as the second CLI argument).

Usage:
    python backtester/generate_sample_data.py --symbol ETHUSDT --timeframe 4h --start 2024-01-01 --end 2024-12-31 --output data/ETHUSDT_4h.csv

"""
from __future__ import annotations
from typing import Optional
import argparse
from datetime import datetime, timedelta
from pathlib import Path
import numpy as np
import pandas as pd


def generate_sample_data(
    symbol: str = "ETHUSDT",
    start_price: float = 2500.0,
    timeframe_minutes: int = 240,
    start_date: str = "2024-01-01",
    end_date: Optional[str] = None,
    volatility: float = 0.02,
    trend: float = 0.0001,
    output_path: str = "data/sample_data.csv",
) -> pd.DataFrame:
    start_time = datetime.fromisoformat(start_date)
    if end_date:
        end_time = datetime.fromisoformat(end_date)
        total_minutes = int((end_time - start_time).total_seconds())
        num_candles = int(total_minutes / timeframe_minutes) + 1
    else:
        # default to one year
        total_minutes = 365 * 24 * 60
        num_candles = int(total_minutes / timeframe_minutes)

    timestamps = [start_time + timedelta(minutes=timeframe_minutes * i) for i in range(num_candles)]

    prices = np.zeros(num_candles)
    prices[0] = start_price
    rng = np.random.default_rng(42)

    for i in range(1, num_candles):
        random_change = rng.normal(trend, volatility)
        prices[i] = max(prices[i-1] * (1 + random_change), 0.01)

    rows = []
    for i in range(num_candles):
        close = prices[i]
        open_p = close * rng.uniform(0.998, 1.002)
        high = max(open_p, close) * rng.uniform(1.0, 1.004)
        low = min(open_p, close) * rng.uniform(0.996, 1.0)
        volume = int(rng.uniform(100000, 2000000))
        rows.append({
            "timestamp": timestamps[i].isoformat(sep=' '),
            "open": round(open_p, 6),
            "high": round(high, 6),
            "low": round(low, 6),
            "close": round(close, 6),
            "volume": volume,
        })

    df = pd.DataFrame(rows)
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)
    print(f"Generated {len(df)} candles for {symbol} -> {out}")
    return df


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--symbol", default="ETHUSDT")
    p.add_argument("--start_price", type=float, default=2500.0)
    p.add_argument("--timeframe", default="4h", help="e.g. 4h, 1h, 15m")
    p.add_argument("--start", dest="start_date", default="2024-01-01")
    p.add_argument("--end", dest="end_date", default=None)
    p.add_argument("--output", default="data/sample_data.csv")
    args = p.parse_args()

    tf = args.timeframe.strip().lower()
    if tf.endswith('h'):
        minutes = int(tf[:-1]) * 60
    elif tf.endswith('m'):
        minutes = int(tf[:-1])
    elif tf.endswith('d'):
        minutes = int(tf[:-1]) * 24 * 60
    else:
        raise SystemExit('Unsupported timeframe')

    generate_sample_data(
        symbol=args.symbol,
        start_price=args.start_price,
        timeframe_minutes=minutes,
        start_date=args.start_date,
        end_date=args.end_date,
        output_path=args.output,
    )
