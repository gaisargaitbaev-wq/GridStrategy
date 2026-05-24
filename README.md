# Grid Strategy Backtester

A modular Python backtester for **Grid Trading Strategies** using the **Mean Reversion Channel (MRC)** indicator from TradingView.

## Overview

This backtester simulates a grid trading strategy where:
1. **Market Order** opens when price touches MRC support/resistance levels (S2/R2)
2. **Safety Orders** (limit orders) are placed at progressively lower/higher prices
3. Positions close when **take-profit** is reached or manually controlled
4. **Martingale** can increase position size on additional safety orders
5. **Dynamic Step** expands the grid span progressively

## Architecture

The project is designed to be **modular and extensible**:

```
GridStrategy/
├── backtester/
│   ├── mrc_indicator.py          # MRC indicator implementation
│   ├── order_manager.py           # Order and trade management
│   ├── grid_engine.py             # Core grid trading logic
│   └── backtest_runner.py         # Main backtesting engine
├── config/
│   └── default_config.json        # Configuration parameters
├── data/
│   └── [OHLCV CSV files]          # Historical price data
├── results/
│   ├── backtest_results.json      # Results summary
│   └── data_with_indicators.csv   # Data with calculated indicators
├── pine-scripts/
│   └── mrc_indicator.pine         # Original TradingView indicator
├── requirements.txt               # Python dependencies
└── README.md                      # This file
```

## Installation

### 1. Clone/Setup Repository
```bash
cd c:\Devops\Git\GridStrategy
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

## Quick Start

### Step 1: Prepare Data

Get OHLCV (Open, High, Low, Close, Volume) historical data in CSV format:

**CSV Format:**
```csv
timestamp,open,high,low,close,volume
2024-01-01 00:00:00,2500.50,2510.75,2498.25,2505.00,1000000
2024-01-01 04:00:00,2505.00,2520.50,2502.00,2515.75,1200000
```

Place your CSV file in the `data/` folder (e.g., `data/ETHUSDT_4h.csv`).

### Step 2: Configure Parameters

Edit `config/default_config.json` with your trading parameters.

### Step 3: Run Backtest

```bash
cd backtester
python backtest_runner.py ../config/default_config.json ../data/ETHUSDT_4h.csv
```

## Configuration Parameters

### Trading Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `cryptocurrency` | string | Asset to trade (e.g., ETHUSDT, SOLUSDT) |
| `direction` | string | Trading direction: "long", "short", or "both" |
| `take_profit_percent` | float | Take-profit % above/below entry |
| `num_safety_orders` | int | Number of limit orders in grid |
| `safety_order_step` | float | Distance between orders in % |
| `martingale` | float | Volume multiplier per order (1.0 = no increase) |
| `dynamic_step` | float | Progressive step expansion in % per order |
| `trading_deposit` | float | Initial trading capital in USD |
| `leverage` | float | Leverage multiplier (1.0 = no leverage) |
| `commission_percent` | float | Trading fees in % |

### Indicator Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `length` | int | MRC lookback period (default 200) |
| `inner_mult` | float | Inner band multiplier (default 1.0) |
| `outer_mult` | float | Outer band multiplier for R2/S2 (default 2.415) |
| `filter_type` | string | Filter type: "SuperSmoother", "EMA", "SMA" |

## Extending the Backtester

### Adding a New Indicator

1. Create a new file: `backtester/your_indicator.py`
2. Implement the indicator class
3. Update `backtest_runner.py` to use your indicator

### Custom Trading Logic

Edit `grid_engine.py` to modify entry/exit conditions.

## Output

Results are saved in the `results/` folder:
- `backtest_results.json` - Detailed trade statistics
- `data_with_indicators.csv` - Price data with MRC levels

## Disclaimer

This backtester is for **educational purposes only**. Past performance does not guarantee future results.