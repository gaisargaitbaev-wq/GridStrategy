#!/usr/bin/env python
"""
Parameter grid search runner for the grid strategy backtester.

Loads the base configuration from config/default_config.json and overrides
specified strategy parameters from config/param_ranges.json. Runs all
combinations and writes results to results/grid_search_results.csv using
semicolon delimiters.
"""
import csv
import json
import os
import sys
from itertools import product
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))

from backtester.backtest_runner import BacktestRunner


DEFAULT_BASE_CONFIG = "config/default_config.json"
DEFAULT_PARAM_RANGES = "config/param_ranges.json"
DEFAULT_OUTPUT_CSV = "results/grid_search_results.csv"


def load_json(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def resolve_data_path(config: dict, cli_data_path: str | None = None) -> str:
    crypto = config.get("cryptocurrency")
    timeframe = config.get("timeframe")
    if not crypto or not timeframe:
        raise ValueError("Both 'cryptocurrency' and 'timeframe' are required in base config")

    cfg_data_path = config.get("data_path", "")
    derived = f"data/{crypto}_{timeframe}.csv"
    data_path = cli_data_path or cfg_data_path or derived

    start_date = config.get("start_date")
    end_date = config.get("end_date")
    if start_date and end_date:
        from backtester.binance_downloader import download_klines

        Path(data_path).parent.mkdir(parents=True, exist_ok=True)
        downloaded_path = download_klines(
            crypto,
            timeframe,
            start_date,
            end_date,
            out_path=data_path,
        )
        data_path = str(downloaded_path)

    if not Path(data_path).exists():
        raise FileNotFoundError(f"Data file not found: {data_path}")

    return data_path


def expand_grid(param_ranges: dict) -> list[dict]:
    keys = sorted(param_ranges.keys())
    values = [param_ranges[k] for k in keys]
    combos = []
    for combo in product(*values):
        combos.append(dict(zip(keys, combo)))
    return combos


def prepare_backtester(base_config_path: str, overrides: dict) -> BacktestRunner:
    backtester = BacktestRunner(base_config_path)
    for key, value in overrides.items():
        backtester.config_dict[key] = value
        if hasattr(backtester.grid_config, key):
            setattr(backtester.grid_config, key, value)
    return backtester


def run_combo(backtester: BacktestRunner, data_path: str) -> dict:
    backtester.load_data(data_path)
    backtester.run_backtest()
    stats = backtester.results["statistics"]
    trades = backtester.results.get("trades", [])
    liquidation_count = sum(1 for trade in trades if trade.get("close_reason") == "liquidation")
    trading_deposit = backtester.config_dict.get("trading_deposit", 0.0)
    final_deposit = trading_deposit + stats.get("total_pnl", 0.0)
    # Compute bot_weight: maximum USDT exposure for a single position if all safety orders filled
    bot_weights = []
    positions = getattr(backtester.grid_engine, "positions", [])
    for pos in positions:
        total_usdt = 0.0
        # market order theoretical value
        try:
            total_usdt += float(pos.position_size) * float(pos.entry_price)
        except Exception:
            pass

        # add all safety orders potential
        for order in getattr(pos, "safety_orders", []):
            try:
                total_usdt += float(order.quantity) * float(order.price)
            except Exception:
                pass

        bot_weights.append(total_usdt)

    bot_weight = max(bot_weights) if bot_weights else 0.0

    return {
        "total_trades": stats.get("total_trades", 0),
        "winning_trades": stats.get("winning_trades", 0),
        "losing_trades": stats.get("losing_trades", 0),
        "win_rate": stats.get("win_rate", 0.0),
        "total_pnl": stats.get("total_pnl", 0.0),
        "avg_pnl": stats.get("avg_pnl", 0.0),
        "avg_pnl_percent": stats.get("avg_pnl_percent", 0.0),
        "liquidations": liquidation_count,
        "final_deposit": final_deposit,
        "bot_weight": bot_weight,
    }


def write_results_csv(output_path: str, rows: list[dict], fieldnames: list[str]) -> None:
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=";")
        writer.writeheader()
        for row in rows:
            output_row = {k: v for k, v in row.items() if k != "leverage"}
            if "leverage" in row:
                output_row["Leverage"] = row["leverage"]
            writer.writerow(output_row)


def main():
    param_file = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_PARAM_RANGES
    base_config_path = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_BASE_CONFIG
    output_path = sys.argv[3] if len(sys.argv) > 3 else DEFAULT_OUTPUT_CSV
    data_path_arg = sys.argv[4] if len(sys.argv) > 4 else None

    param_ranges = load_json(param_file)
    combos = expand_grid(param_ranges)
    if not combos:
        raise SystemExit("No parameter combinations found in param_ranges.json")

    base_config = load_json(base_config_path)
    data_path = resolve_data_path(base_config, data_path_arg)

    rows = []
    fieldnames = [
        *["Leverage" if key == "leverage" else key for key in sorted(param_ranges.keys())],
        "TOP",
        "total_trades",
        "winning_trades",
        "losing_trades",
        "win_rate",
        "total_pnl",
        "avg_pnl",
        "avg_pnl_percent",
        "liquidations",
        "final_deposit",
        "bot_weight"
    ]

    print(f"Running grid search: {len(combos)} combinations")
    for idx, combo in enumerate(combos, start=1):
        print(f"[{idx}/{len(combos)}] {combo}")
        backtester = prepare_backtester(base_config_path, combo)
        result = run_combo(backtester, data_path)
        row = {**combo, **result, "TOP": False}
        rows.append(row)

    top_count = min(10, len(rows))
    for row in sorted(rows, key=lambda r: r["total_pnl"], reverse=True)[:top_count]:
        row["TOP"] = True

    write_results_csv(output_path, rows, fieldnames)
    print(f"\nGrid search completed. Results written to: {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
