# Getting Started with Grid Strategy Backtester

## 5-Minute Quick Start

### 1. Install Dependencies
```bash
cd GridStrategy
pip install -r requirements.txt
```

### 2. Optional: Generate Sample Data (for testing)
This step is optional. If you want synthetic data for quick testing, run the standalone generator:
```bash
cd backtester
python generate_sample_data.py --symbol ETHUSDT --timeframe 4h --start 2024-01-01 --end 2024-12-31 --output ../data/ETHUSDT_4h.csv
# Creates: ../data/ETHUSDT_4h.csv
```

If `config/default_config.json` has `data_path` empty, `run_backtest.py` will derive the expected CSV path from `cryptocurrency` and `timeframe` and will automatically download missing data from Binance using `start_date` and `end_date`.

### 3. Run Backtest
```bash
python -c "from backtest_runner import BacktestRunner; \
b = BacktestRunner('../config/default_config.json'); \
  b.load_data('../data/your_data.csv'); \
results = b.run_backtest(); \
b.print_summary()"
```

**Or use the quick-start script:**
```bash
cd ..
python run_backtest.py
```

---

## Full Setup Guide

### Prerequisites
- Python 3.8+
- pip (Python package manager)

### Step 1: Install Requirements

```bash
cd GridStrategy
pip install -r requirements.txt
```

**Installed packages:**
- `pandas` - Data manipulation
- `numpy` - Numerical computing
- `python-dateutil` - Date utilities

### Step 2: Prepare Your Data

The backtester requires OHLCV (Open, High, Low, Close, Volume) data in CSV format.

**CSV Format:**
```csv
timestamp,open,high,low,close,volume
2024-01-01 00:00:00,2500.50,2510.75,2498.25,2505.00,1000000
2024-01-01 04:00:00,2505.00,2520.50,2502.00,2515.75,1200000
2024-01-02 00:00:00,2515.75,2530.20,2510.00,2525.50,1150000
```

**Options for getting data:**

#### A. Optional: Generate Sample Data (for testing)
```bash
cd backtester
python generate_sample_data.py --symbol ETHUSDT --timeframe 4h --start 2024-01-01 --end 2024-12-31 --output ../data/ETHUSDT_4h.csv
# Creates: ../data/ETHUSDT_4h.csv
```

#### B. Download Real Data
- **Binance**: Export from TradingView chart
- **Bybit API**: Use `ccxt` library
  ```python
  import ccxt
  exchange = ccxt.bybit()
  ohlcv = exchange.fetch_ohlcv('ETH/USDT', '4h', limit=365)
  ```
- **CSV Files**: Place in `data/` folder

### Step 3: Configure Trading Parameters

Edit `config/default_config.json`:

```json
{
  "cryptocurrency": "ETHUSDT",
  "timeframe": "4h",
  "direction": "both",
  "take_profit_percent": 2.0,
  "num_safety_orders": 5,
  "safety_order_step": 1.5,
  "martingale": 1.5,
  "dynamic_step": 0.5,
  "trading_deposit": 1000.0,
  "first_order_price": 10.0,
  "leverage": 1.0,
  "commission_percent": 0.1,
  "indicator_config": {
    "length": 200,
    "inner_mult": 1.0,
    "outer_mult": 2.415,
    "filter_type": "SuperSmoother"
  }
}
```

### Step 4: Run Backtest

#### Option A: Quick Run Script
```bash
python run_backtest.py
```

#### Option B: Manual Execution
```bash
cd backtester
python backtest_runner.py ../config/default_config.json ../data/your_data.csv
```

If the CSV is missing and you want `run_backtest.py` to download it automatically, leave `data_path` empty in `config/default_config.json` and set `cryptocurrency`, `timeframe`, `start_date`, and `end_date` there.

#### Option C: Python Script
```python
from backtester.backtest_runner import BacktestRunner

backtester = BacktestRunner("config/default_config.json")
backtester.load_data("data/ETHUSDT_4h.csv")
results = backtester.run_backtest()
backtester.print_summary()
backtester.save_results("results/backtest_results.json")
```

### Step 5: Review Results

Results are saved to `results/`:

**backtest_results.json:**
```json
{
  "statistics": {
    "total_trades": 45,
    "winning_trades": 32,
    "losing_trades": 13,
    "win_rate": 71.11,
    "total_pnl": 245.67,
    "avg_pnl": 5.46,
    "avg_pnl_percent": 2.12,
    "max_pnl": 50.25,
    "min_pnl": -15.80
  },
  "trades": [...]
}
```

**data_with_indicators.csv:**
- Original OHLCV data
- MRC levels (meanline, r1, s1, r2, s2)
- Trading signals (condition)

---

## Configuration Guide

### Trading Direction

**long**: Only BUY when price touches S2
```json
"direction": "long"
```

**short**: Only SELL when price touches R2
```json
"direction": "short"
```

**both**: Trade in both directions
```json
"direction": "both"
```

### Grid Parameters

**Example 1: Conservative (Low Risk)**
```json
{
  "take_profit_percent": 1.0,
  "num_safety_orders": 3,
  "safety_order_step": 2.0,
  "martingale": 1.0,
  "dynamic_step": 0.0,
  "leverage": 1.0
}
```

**Example 2: Aggressive (High Risk)**
```json
{
  "take_profit_percent": 5.0,
  "num_safety_orders": 10,
  "safety_order_step": 0.5,
  "martingale": 2.0,
  "dynamic_step": 0.3,
  "leverage": 3.0
}
```

**Example 3: Balanced**
```json
{
  "take_profit_percent": 2.5,
  "num_safety_orders": 5,
  "safety_order_step": 1.5,
  "martingale": 1.5,
  "dynamic_step": 0.5,
  "leverage": 1.5
}
```

---

## Understanding MRC Signals

The Mean Reversion Channel (MRC) indicator produces **condition values** that signal market states:

| Condition | Signal | Meaning |
|-----------|--------|---------|
| -3 | Strong Oversold | Price below S2 (Strong BUY) |
| -2 | Oversold | Price at S2 (BUY) |
| -1 | Weak Oversold | Between S1 and S2 |
| 0 | Neutral | At mean line |
| 1 | Weak Overbought | Between R1 and R2 |
| 2 | Overbought | At R2 (SELL) |
| 3 | Strong Overbought | Above R2 (Strong SELL) |

**Trading Logic:**
- **BUY** when condition ≤ -2 (price crosses S2)
- **SELL** when condition ≥ 2 (price crosses R2)

---

## Grid Order Example

**Setup:**
```json
{
  "entry_price": 2500,
  "take_profit": 2.0,
  "num_orders": 5,
  "step": 1.5,
  "martingale": 1.5
}
```

**BUY Grid:**
```
Market Order:      $2500.00 (1.0x volume)
├─ Safety Order 1: $2462.50 (1.0x volume) - 1.5% below entry
├─ Safety Order 2: $2425.42 (1.5x volume) - 1.5% below prev
├─ Safety Order 3: $2389.15 (2.25x volume) - 1.5% below prev
├─ Safety Order 4: $2353.60 (3.375x volume) - 1.5% below prev
└─ Safety Order 5: $2318.72 (5.06x volume) - 1.5% below prev

Take-Profit:       $2550.00 (entry + 2%)
```

---

## Troubleshooting

### No Trades Generated

**Check:**
1. Data has correct columns (timestamp, open, high, low, close, volume)
2. Date range is reasonable (not too short)
3. Prices include S2/R2 crossovers
4. Try adjusting `take_profit_percent` lower

**Solution:**
```bash
# Check first few rows of data
python -c "import pandas as pd; df = pd.read_csv('data/your_data.csv'); print(df.head())"
```

### High Drawdown

**Reduce Risk:**
- Lower `martingale` (e.g., 1.0 instead of 2.0)
- Increase `safety_order_step` (e.g., 2.0 instead of 1.5)
- Reduce `leverage` (e.g., 1.0 instead of 2.0)
- Lower `num_safety_orders` (e.g., 3 instead of 10)

### Data Format Errors

**Expected CSV format:**
```
timestamp,open,high,low,close,volume
```

**Invalid formats:**
- Missing columns ❌
- Different column order (order matters)
- Timestamps not parseable (use YYYY-MM-DD HH:MM:SS)

---

## Next Steps

1. **Customize the Strategy**: See [CUSTOMIZATION.md](CUSTOMIZATION.md)
2. **Try Different Indicators**: Implement Bollinger Bands, RSI, MACD
3. **Optimize Parameters**: Backtest multiple configurations
4. **Paper Trading**: Test on paper accounts before live trading
5. **Live Trading**: Implement the strategy on your exchange

---

## Important Notes

⚠️ **This is for educational purposes only**
- Past performance ≠ Future results
- Always test extensively before trading
- Start with small position sizes
- Never risk money you can't afford to lose
- Implement proper risk management

---

## Support

For issues:
1. Check configuration parameters
2. Verify data format
3. Review logs in console output
4. Check CUSTOMIZATION.md for advanced usage
5. See README.md for detailed documentation
