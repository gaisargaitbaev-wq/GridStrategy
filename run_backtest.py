#!/usr/bin/env python
"""
Quick Start Script - Run backtest
"""
import sys
import os
from pathlib import Path

# Use package imports for the backtester module
sys.path.insert(0, os.path.dirname(__file__))

from backtester.backtest_runner import BacktestRunner  # noqa: E402
from backtester.binance_downloader import download_klines  # noqa: E402


def timeframe_to_minutes(timeframe: str) -> int:
    """Convert timeframe strings like '4h', '1h', '15m', '1d' to minutes."""
    timeframe = timeframe.strip().lower()
    if timeframe.endswith("m"):
        return int(timeframe[:-1])
    if timeframe.endswith("h"):
        return int(timeframe[:-1]) * 60
    if timeframe.endswith("d"):
        return int(timeframe[:-1]) * 24 * 60
    raise ValueError(f"Unsupported timeframe: {timeframe}")


def main():
    print("="*60)
    print("GRID STRATEGY BACKTESTER - QUICK START")
    print("="*60)

    # Step 1: Load configuration and require real data
    backtester = BacktestRunner("config/default_config.json")
    config = backtester.config_dict

    # Expect a real data path in config or as CLI arg. If empty, derive from
    # cryptocurrency and timeframe.
    cli_data_path = sys.argv[2] if len(sys.argv) > 2 else None
    cfg_data_path = config.get('data_path', '')

    crypto = config.get('cryptocurrency')
    timeframe = config.get('timeframe')
    if not crypto or not timeframe:
        raise SystemExit(
            "Error: 'cryptocurrency' or 'timeframe' missing in config"
        )

    derived = f"data/{crypto}_{timeframe}.csv"
    data_path = cli_data_path or cfg_data_path or derived

    # Ensure source data covers requested range: use downloader to create/merge cache
    start_date = config.get('start_date')
    end_date = config.get('end_date')
    if start_date and end_date:
        print(f"\nEnsuring data for {crypto} {timeframe} from {start_date} to {end_date}")
        Path(data_path).parent.mkdir(parents=True, exist_ok=True)
        try:
            downloaded_path = download_klines(
                crypto,
                timeframe,
                start_date,
                end_date,
                out_path=data_path,
            )
            data_path = str(downloaded_path)
        except Exception as download_error:
            raise SystemExit(
                "Error downloading data for {} {}: {}".format(
                    crypto,
                    timeframe,
                    download_error,
                )
            )

        if not Path(data_path).exists():
            raise SystemExit(
                "Error: data file still not found after download: {}".format(
                    data_path,
                )
            )

    print("\n1. Using data file:", data_path)
    print("\n2. Running backtest with provided data...")

    try:
        backtester.load_data(data_path)
        backtester.run_backtest()

        # Save results
        backtester.save_results("results/backtest_results.json")
        data_out = "results/data_with_indicators.csv"
        backtester.save_data_with_indicators(data_out)
        backtester.plot_results("results/backtest_chart.png")

        # Print summary
        backtester.print_summary()

        print("\n\u2713 Backtest completed successfully!")
        print("\nResults saved to:")
        print("  - results/backtest_results.json")
        print(f"  - {data_out}")

    except Exception as e:
        print(f"\n✗ Error running backtest: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
