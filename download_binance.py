"""CLI wrapper to download Binance klines into data/ using the downloader module."""
from backtester.binance_downloader import download_klines


def main():
    import argparse

    p = argparse.ArgumentParser(description='Download Binance historical data with caching')
    p.add_argument('--symbol', required=True, help='Trading pair symbol, e.g. ETHUSDT')
    p.add_argument('--interval', required=True, help='Kline interval, e.g. 4h, 1h, 1d')
    p.add_argument('--start', required=True, help='Start date (YYYY-MM-DD)')
    p.add_argument('--end', required=True, help='End date (YYYY-MM-DD)')
    p.add_argument('--out', required=False, help='Optional output CSV path')
    args = p.parse_args()

    out = download_klines(args.symbol, args.interval, args.start, args.end, out_path=args.out)
    print(f'Download complete: {out}')


if __name__ == '__main__':
    main()
