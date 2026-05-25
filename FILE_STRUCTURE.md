# Project File Structure & Explanation

## Directory Tree

```
GridStrategy/
│
├── 📋 Documentation Files
│   ├── README.md                          ← Technical reference
│   ├── GETTING_STARTED.md                 ← 5-minute setup guide
│   ├── CUSTOMIZATION.md                   ← How to add features
│   ├── PROJECT_SUMMARY.md                 ← Visual overview
│   └── SETUP_COMPLETE.md                  ← This setup is complete
│
├── 🚀 Execution Files
│   ├── run_backtest.py                    ← Quick-start script (python run_backtest.py)
│   └── validate.py                        ← Validation checker (python validate.py)
│
├── ⚙️ Configuration
│   ├── requirements.txt                   ← Python packages (pip install -r requirements.txt)
│   └── .gitignore                         ← Git ignore rules
│
├── 📂 backtester/                         ← Core backtesting system
│   ├── __init__.py                        ← Package initialization
│   │
│   ├── mrc_indicator.py                   ← MRC Indicator
│   │   ├── SuperSmoother class            ├─ Smoothing filter
│   │   └── MRCIndicator class             ├─ Main indicator
│   │                                      └─ Outputs: meanline, R1/S1/R2/S2, signals
│   │
│   ├── order_manager.py                   ← Order & Trade Management
│   │   ├── OrderType enum                 ├─ MARKET, LIMIT
│   │   ├── OrderSide enum                 ├─ BUY, SELL
│   │   ├── Order class                    ├─ Individual order
│   │   ├── Trade class                    ├─ Completed trade (entry + exit)
│   │   └── OrderManager class             └─ Manages all orders/trades/stats
│   │
│   ├── grid_engine.py                     ← Grid Trading Logic
│   │   ├── GridConfig dataclass           ├─ Configuration
│   │   ├── GridPosition class             ├─ Single position
│   │   │   ├── open_market_order()        ├─ Opens entry
│   │   │   ├── open_safety_orders()       ├─ Creates grid
│   │   │   ├── check_safety_fills()       ├─ Monitor fills
│   │   │   └── check_take_profit()        └─ Monitor exit
│   │   └── GridEngine class               └─ Manages all positions
│   │
│   ├── backtest_runner.py                 ← Main Backtesting Engine
│   │   ├── BacktestRunner class           ├─ Main orchestrator
│   │   ├── load_data()                    ├─ Load CSV
│   │   ├── run_backtest()                 ├─ Execute simulation
│   │   ├── _simulate_trading()            ├─ Candle-by-candle logic
│   │   └── generate_results()             └─ Create report
│   │
│   └── generate_sample_data.py            ← Optional Test Data Generator
│       └── generate_sample_data()         └─ Create synthetic OHLCV (optional)
│
├── 📂 config/                             ← Configuration Files
│   └── default_config.json                ← Your 12 trading parameters
│       ├── Cryptocurrency                 ├─ What to trade
│       ├── Timeframe                      ├─ Candle period
│       ├── Direction                      ├─ long/short/both
│       ├── Grid parameters                ├─ TP, orders, step, martingale
│       ├── Position parameters            ├─ Deposit, leverage
│       └── Indicator config               └─ MRC settings
│
├── 📂 data/                               ← Price Data (Input)
│   └── [your OHLCV CSV files]             ← Place your historical data here
│       ├── timestamp                      ├─ ISO format datetime
│       ├── open                           ├─ Opening price
│       ├── high                           ├─ Highest price
│       ├── low                            ├─ Lowest price
│       ├── close                          ├─ Closing price
│       └── volume                         └─ Trading volume
│
├── 📂 results/                            ← Backtest Results (Output)
│   ├── backtest_results.json              ├─ Trade statistics
│   │   ├── statistics                     ├─ Win rate, PnL, etc.
│   │   └── trades                         └─ Individual trade details
│   │
│   └── data_with_indicators.csv           ├─ Original data + indicators
│       ├── OHLCV columns                  ├─ Price data
│       ├── meanline, r1, s1, r2, s2       ├─ MRC levels
│       └── condition                      └─ Trading signals
│
├── 📂 pine-scripts/                       ← TradingView Code
│   └── mrc_indicator.pine                 ← Original MRC indicator
│
└── .git/                                  ← Git repository
```

---

## File Purposes

### 📋 Documentation

| File | Purpose |
|------|---------|
| **README.md** | Complete technical reference with all parameters |
| **GETTING_STARTED.md** | Step-by-step setup guide for beginners |
| **CUSTOMIZATION.md** | How to add custom indicators (RSI, BB, MACD, etc.) |
| **PROJECT_SUMMARY.md** | Visual project overview with examples |
| **SETUP_COMPLETE.md** | Setup confirmation (what you just read) |

### 🚀 Executable Scripts

| File | Command | Purpose |
|------|---------|---------|
| **run_backtest.py** | `python run_backtest.py` | Quick-start (runs backtest using config/data_path) |
| **validate.py** | `python validate.py` | Verify all modules work |
| **backtest_runner.py** | `python backtest_runner.py config.json data.csv` | Manual backtest run |
| **generate_sample_data.py** | `python backtester/generate_sample_data.py` | Optional: generate test data |

### ⚙️ Core Classes

#### `mrc_indicator.py`
```python
MRCIndicator(length=200, inner_mult=1.0, outer_mult=2.415)
  ↓
  calculate(close, high, low, true_range)
  ↓
  Returns: (meanline, meanrange, r1, s1, r2, s2, signals)
```

#### `order_manager.py`
```python
OrderManager(commission_percent=0.1)
  ├── create_order() → Order
  ├── fill_order() → fills order
  ├── close_order() → calculates PnL
  ├── create_trade() → completed trade
  └── get_statistics() → returns dict with stats
```

#### `grid_engine.py`
```python
GridEngine(GridConfig)
  ├── open_position() → GridPosition
  └── GridPosition
      ├── open_market_order() → market entry
      ├── open_safety_orders() → creates grid
      ├── check_safety_order_fills() → monitor fills
      ├── check_take_profit() → check exit
      └── close_position() → close and calculate PnL
```

#### `backtest_runner.py`
```python
BacktestRunner(config_path)
  ├── load_data(csv_path) → load OHLCV
  ├── run_backtest() → execute simulation
  ├── save_results(path) → save JSON
  ├── save_data_with_indicators(path) → save CSV with MRC
  └── print_summary() → display stats
```

---

## Data Flow

### Input → Processing → Output

```
┌─────────────────────────────────────────────────────────┐
│ 1. INPUT: OHLCV Price Data (CSV)                         │
│    ├─ timestamp                                          │
│    ├─ open, high, low, close                            │
│    └─ volume                                            │
└──────────────────┬──────────────────────────────────────┘
                   ↓
┌──────────────────────────────────────────────────────────┐
│ 2. CALCULATION: MRC Indicator                             │
│    ├─ Meanline (center)                                 │
│    ├─ True Range                                        │
│    ├─ R1/S1 (inner bands)                              │
│    └─ R2/S2 (outer bands) + Signals                    │
└──────────────────┬──────────────────────────────────────┘
                   ↓
┌──────────────────────────────────────────────────────────┐
│ 3. SIMULATION: For Each Candle                            │
│    ├─ Check if price crosses S2/R2                      │
│    ├─ Open position with market order                   │
│    ├─ Open grid of safety orders                        │
│    ├─ Monitor fills as price moves                      │
│    ├─ Check if take-profit is hit                       │
│    ├─ Close position and calculate PnL                  │
│    └─ Record trade statistics                           │
└──────────────────┬──────────────────────────────────────┘
                   ↓
┌──────────────────────────────────────────────────────────┐
│ 4. OUTPUT: Results                                        │
│    ├─ backtest_results.json                             │
│    │   ├─ Total trades, win rate, PnL                   │
│    │   └─ Individual trade details                      │
│    └─ data_with_indicators.csv                          │
│        ├─ Original OHLCV data                           │
│        ├─ MRC levels (meanline, r1, s1, r2, s2)        │
│        └─ Trading signals (condition)                   │
└──────────────────────────────────────────────────────────┘
```

---

## Configuration Flow

```
config/default_config.json
         ↓
BacktestRunner.__init__()
    ├─ GridConfig (trading parameters)
    ├─ MRCIndicator (indicator settings)
    └─ GridEngine (manages positions)
         ↓
    run_backtest()
         ↓
    Simulation loop (for each candle)
```

---

## Module Dependencies

```
backtest_runner.py (Main)
    ├── imports mrc_indicator.py
    ├── imports grid_engine.py
    │   └── imports order_manager.py
    └── imports generate_sample_data.py (optional)

grid_engine.py
    └── imports order_manager.py
```

---

## How to Navigate the Project

### 1. **First Time Setup**
   → Start with `GETTING_STARTED.md`

### 2. **Want to Run Backtest**
   → Use `python run_backtest.py`

### 3. **Have Your Own Data**
   → See `GETTING_STARTED.md` → Step 2

### 4. **Want to Customize Parameters**
   → Edit `config/default_config.json`

### 5. **Want to Add Indicator**
   → See `CUSTOMIZATION.md` → Section 1

### 6. **Want to Modify Trading Logic**
   → See `CUSTOMIZATION.md` → Section 2

### 7. **Troubleshooting**
   → See `README.md` → Troubleshooting section

---

## Quick Reference

### Run Backtest
```bash
python run_backtest.py
```

### Validate Installation
```bash
python validate.py
```

### Generate Test Data (optional)
```bash
cd backtester
python generate_sample_data.py --symbol ETHUSDT --timeframe 4h --start 2024-01-01 --end 2024-12-31 --output ../data/ETHUSDT_4h.csv
```

### Run with Custom Data
```bash
cd backtester
python backtest_runner.py ../config/default_config.json ../data/YOUR_FILE.csv
```

---

## Key Concepts

### GridConfig (12 Parameters)
```json
{
  "cryptocurrency": "trading pair",
  "timeframe": "candle period",
  "direction": "long/short/both",
  "take_profit_percent": "target %",
  "num_safety_orders": "grid levels",
  "safety_order_step": "distance %",
  "martingale": "volume multiplier",
  "dynamic_step": "progressive increase",
  "trading_deposit": "capital $",
  "first_order_price": "first order leveraged volume $",
  "leverage": "position multiplier",
  "commission_percent": "fees %"
}
```

### MRC Signals (-3 to 3)
```
3: Strong Overbought (SELL)
2: Overbought (SELL at R2)
1: Weak Overbought
0: Neutral
-1: Weak Oversold
-2: Oversold (BUY at S2)
-3: Strong Oversold (BUY)
```

### Order Types
- **Market Order** - Entry, executed immediately
- **Limit Orders** - Safety orders, filled when price reaches level
- **Filled** - Order completed
- **Pending** - Waiting to fill
- **Cancelled** - Closed without filling

---

## Extending the Project

### Add New Indicator
1. Create `backtester/your_indicator.py`
2. Update `backtest_runner.py` to import it
3. Modify `config/default_config.json`

### Modify Trading Rules
1. Edit `grid_engine.py` methods
2. Change entry/exit logic
3. Add stop-loss rules
4. Test with backtest

### Optimize Parameters
1. Test different configs
2. Save results for comparison
3. Find best parameters

---

## Files You'll Modify

### During Setup
- None required (ready to use)

### To Backtest
- `config/default_config.json` (your parameters)
- Place your CSV in `data/` folder

### To Customize
- `backtester/grid_engine.py` (trading logic)
- `backtester/backtest_runner.py` (entry signals)
- Create new indicator files

---

## Remember

- **All files have docstrings** - Read them for details
- **Code is modular** - Easy to swap components
- **Well-organized** - Clear separation of concerns
- **Ready to extend** - Add features without breaking anything

Happy backtesting! 🚀
