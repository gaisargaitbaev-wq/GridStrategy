"""Binance Klines downloader with simple local caching.

This module fetches historical klines (OHLCV) from Binance REST API in multiple
requests (since Binance limits 1000 candles per request) and writes a CSV to
the `data/` folder. If a cache file exists for the given symbol/interval it
will only fetch missing ranges and merge into the cache.

Usage:
    from backtester.binance_downloader import download_klines
    download_klines('ETHUSDT', '4h', '2024-01-01', '2024-12-31')
"""
from __future__ import annotations

import time
import requests
import pandas as pd
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional


API_URL = "https://api.binance.com/api/v3/klines"
MAX_LIMIT = 1000


def _to_ms(dt: datetime) -> int:
    return int(dt.replace(tzinfo=timezone.utc).timestamp() * 1000)


def _parse_dt(s: str) -> datetime:
    # Accept YYYY-MM-DD or full ISO
    try:
        return datetime.fromisoformat(s)
    except Exception:
        return datetime.strptime(s, "%Y-%m-%d")


def fetch_klines_range(symbol: str, interval: str, start_ms: int, end_ms: int) -> pd.DataFrame:
    """Fetch klines between start_ms and end_ms (inclusive) using multiple requests."""
    rows = []
    cur_start = start_ms

    while cur_start <= end_ms:
        params = {
            'symbol': symbol,
            'interval': interval,
            'startTime': cur_start,
            'endTime': end_ms,
            'limit': MAX_LIMIT
        }
        resp = requests.get(API_URL, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        if not data:
            break

        rows.extend(data)

        # move to next batch: last kline close time + 1 ms
        last_close_time = data[-1][6]
        # If the last returned candle's open time equals cur_start, avoid infinite loop
        if data[-1][0] <= cur_start and len(data) < MAX_LIMIT:
            break
        cur_start = last_close_time + 1

        # be nice to API
        time.sleep(0.2)

    if not rows:
        return pd.DataFrame(columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])

    df = pd.DataFrame([{
        'timestamp': datetime.utcfromtimestamp(int(r[0]) / 1000).strftime('%Y-%m-%d %H:%M:%S'),
        'open': float(r[1]),
        'high': float(r[2]),
        'low': float(r[3]),
        'close': float(r[4]),
        'volume': float(r[5])
    } for r in rows])

    # dedupe and sort
    df = df.drop_duplicates(subset=['timestamp']).sort_values('timestamp').reset_index(drop=True)
    return df


def download_klines(symbol: str,
                    interval: str,
                    start: str,
                    end: str,
                    out_path: Optional[str] = None,
                    cache: bool = True) -> Path:
    """Download klines and save to CSV. Returns the path to the CSV file.

    - `symbol`: e.g. 'ETHUSDT'
    - `interval`: Binance interval string, e.g. '4h', '1h', '1d'
    - `start` and `end`: date strings (YYYY-MM-DD or ISO)
    - `out_path`: optional output CSV path; if omitted, writes to `data/{symbol}_{interval}.csv`
    - `cache`: if True, will merge results with existing cache file and only fetch missing ranges
    """
    start_dt = _parse_dt(start)
    end_dt = _parse_dt(end)
    start_ms = _to_ms(start_dt)
    end_ms = _to_ms(end_dt)

    data_dir = Path('data')
    data_dir.mkdir(parents=True, exist_ok=True)

    cache_file = Path(out_path) if out_path else data_dir / f"{symbol}_{interval}.csv"

    # If caching and file exists, determine missing ranges
    if cache and cache_file.exists():
        df_cache = pd.read_csv(cache_file)
        if 'timestamp' in df_cache.columns:
            df_cache['timestamp'] = pd.to_datetime(df_cache['timestamp'])
            cached_start = int(df_cache['timestamp'].min().timestamp() * 1000)
            cached_end = int(df_cache['timestamp'].max().timestamp() * 1000)
        else:
            cached_start = None
            cached_end = None
    else:
        df_cache = None
        cached_start = None
        cached_end = None

    to_fetch = []
    if cached_start is None:
        to_fetch.append((start_ms, end_ms))
    else:
        # before cached range
        if start_ms < cached_start:
            to_fetch.append((start_ms, cached_start - 1))
        # after cached range
        if end_ms > cached_end:
            to_fetch.append((cached_end + 1, end_ms))

    fetched_parts = []
    for s_ms, e_ms in to_fetch:
        df_part = fetch_klines_range(symbol, interval, s_ms, e_ms)
        if not df_part.empty:
            fetched_parts.append(df_part)

    if df_cache is None:
        if fetched_parts:
            df_all = pd.concat(fetched_parts, axis=0, ignore_index=True)
        else:
            df_all = pd.DataFrame(columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    else:
        parts = [df_cache]
        parts.extend(fetched_parts)
        df_all = pd.concat(parts, axis=0, ignore_index=True)

    if not df_all.empty:
        df_all['timestamp'] = pd.to_datetime(df_all['timestamp'])
        df_all = df_all.drop_duplicates(subset=['timestamp']).sort_values('timestamp').reset_index(drop=True)
        df_all.to_csv(cache_file, index=False)

    return cache_file


if __name__ == '__main__':
    import argparse

    p = argparse.ArgumentParser(description='Download Binance klines with caching')
    p.add_argument('--symbol', required=True)
    p.add_argument('--interval', required=True)
    p.add_argument('--start', required=True)
    p.add_argument('--end', required=True)
    p.add_argument('--out', required=False)
    args = p.parse_args()

    path = download_klines(args.symbol, args.interval, args.start, args.end, out_path=args.out)
    print(f'Data saved to: {path}')
