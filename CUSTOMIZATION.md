# Customization Guide

This guide explains how to extend and customize the Grid Strategy Backtester.

## 1. Adding a Custom Indicator

The backtester is designed to be indicator-agnostic. You can easily swap the MRC indicator for another indicator.

### Step 1: Create Your Indicator Class

Create a new file `backtester/your_indicator.py`:

```python
import numpy as np
from typing import Tuple

class YourIndicator:
    """Your custom indicator"""
    
    def __init__(self, param1: int = 20, param2: float = 1.5):
        """
        Initialize indicator
        
        Args:
            param1: Your parameter 1
            param2: Your parameter 2
        """
        self.param1 = param1
        self.param2 = param2
    
    def calculate(
        self,
        close: np.ndarray,
        high: np.ndarray,
        low: np.ndarray,
        true_range: np.ndarray = None
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        Calculate indicator values
        
        Args:
            close: Close prices
            high: High prices
            low: Low prices
            true_range: True Range (optional)
            
        Returns:
            Tuple of indicator values
        """
        # Your indicator calculation logic here
        
        # Must return 7 arrays in this order:
        # (trend_line, volatility, upper_band1, lower_band1, upper_band2, lower_band2, signal)
        
        trend_line = self._calculate_trend(close)
        volatility = self._calculate_volatility(close)
        upper_band1 = trend_line + (volatility * 1.0)
        lower_band1 = trend_line - (volatility * 1.0)
        upper_band2 = trend_line + (volatility * 2.0)
        lower_band2 = trend_line - (volatility * 2.0)
        signal = self._calculate_signal(close, trend_line)
        
        return trend_line, volatility, upper_band1, lower_band1, upper_band2, lower_band2, signal
    
    def _calculate_trend(self, data: np.ndarray) -> np.ndarray:
        """Calculate trend line"""
        # Implementation here
        pass
    
    def _calculate_volatility(self, data: np.ndarray) -> np.ndarray:
        """Calculate volatility"""
        # Implementation here
        pass
    
    def _calculate_signal(self, close: np.ndarray, trend: np.ndarray) -> np.ndarray:
        """
        Calculate signal (-3 to 3)
        
        Returns:
            condition array where:
            3: Strong Overbought
            2: Overbought (at upper band 2)
            1: Weak Overbought (between bands)
            0: Neutral
            -1: Weak Oversold
            -2: Oversold (at lower band 2)
            -3: Strong Oversold
        """
        # Implementation here
        pass
```

### Step 2: Update backtest_runner.py

In `backtest_runner.py`, import and use your indicator:

```python
# Replace:
from mrc_indicator import MRCIndicator

# With:
from your_indicator import YourIndicator

# In __init__:
# Replace:
self.indicator = MRCIndicator(...)

# With:
self.indicator = YourIndicator(
    param1=config_dict['indicator_config'].get('param1', 20),
    param2=config_dict['indicator_config'].get('param2', 1.5)
)
```

### Step 3: Update Configuration

Update `config/default_config.json`:

```json
{
  ...
  "indicator_config": {
    "param1": 20,
    "param2": 1.5
  }
}
```

## 2. Modifying Trading Logic

Edit `grid_engine.py` to customize entry/exit rules.

### Custom Entry Signals

Modify the `_get_entry_signal()` method in `backtest_runner.py`:

```python
def _get_entry_signal(self, condition: int) -> Optional[OrderSide]:
    """Get entry signal from indicator"""
    
    # Your custom logic here
    if condition <= -2:  # Oversold
        return OrderSide.BUY
    elif condition >= 2:  # Overbought
        return OrderSide.SELL
    
    return None
```

### Custom Exit Signals

Modify `check_take_profit()` in `grid_engine.py`:

```python
def check_take_profit(self, current_price: float) -> bool:
    """Check exit condition"""
    
    # Default: TP percentage
    tp_price = self._calculate_tp_price()
    
    if self.side == OrderSide.BUY:
        return current_price >= tp_price
    else:
        return current_price <= tp_price
```

Add custom exit logic:

```python
def check_stop_loss(self, current_price: float) -> bool:
    """Check stop-loss condition"""
    
    avg_entry = self.get_average_entry_price()
    sl_percent = 5.0  # 5% stop-loss
    
    if self.side == OrderSide.BUY:
        return current_price <= avg_entry * (1 - sl_percent / 100)
    else:
        return current_price >= avg_entry * (1 + sl_percent / 100)
```

## 3. Popular Indicator Examples

### Bollinger Bands

```python
class BollingerBands:
    def __init__(self, length: int = 20, num_std: float = 2.0):
        self.length = length
        self.num_std = num_std
    
    def calculate(self, close, high, low, tr=None):
        sma = pd.Series(close).rolling(self.length).mean().values
        std = pd.Series(close).rolling(self.length).std().values
        
        upper = sma + (std * self.num_std)
        lower = sma - (std * self.num_std)
        
        signal = np.where(close > upper, 2, np.where(close < lower, -2, 0))
        
        return sma, std, upper, lower, upper, lower, signal
```

### RSI (Relative Strength Index)

```python
class RSI:
    def __init__(self, length: int = 14):
        self.length = length
    
    def calculate(self, close, high, low, tr=None):
        delta = np.diff(close)
        gains = np.where(delta > 0, delta, 0)
        losses = np.where(delta < 0, -delta, 0)
        
        avg_gain = pd.Series(gains).rolling(self.length).mean().values
        avg_loss = pd.Series(losses).rolling(self.length).mean().values
        
        rs = avg_gain / (avg_loss + 1e-10)
        rsi = 100 - (100 / (1 + rs))
        
        # Generate bands at 30/70
        signal = np.where(rsi > 70, 2, np.where(rsi < 30, -2, 0))
        
        return rsi, rsi, rsi, rsi, rsi, rsi, signal
```

### MACD (Moving Average Convergence Divergence)

```python
class MACD:
    def __init__(self, fast: int = 12, slow: int = 26, signal: int = 9):
        self.fast = fast
        self.slow = slow
        self.signal = signal
    
    def calculate(self, close, high, low, tr=None):
        ema_fast = self._ema(close, self.fast)
        ema_slow = self._ema(close, self.slow)
        macd = ema_fast - ema_slow
        signal_line = self._ema(macd, self.signal)
        histogram = macd - signal_line
        
        signal = np.where(histogram > 0, 1, np.where(histogram < 0, -1, 0))
        
        return macd, histogram, signal_line, signal_line, macd, macd, signal
    
    @staticmethod
    def _ema(data, span):
        return pd.Series(data).ewm(span=span).mean().values
```

## 4. Advanced Customization

### Multi-Indicator Strategy

Combine multiple indicators:

```python
class MultiIndicatorStrategy:
    def __init__(self):
        self.mrc = MRCIndicator()
        self.rsi = RSI()
    
    def calculate(self, close, high, low, tr):
        mrc_result = self.mrc.calculate(close, high, low, tr)
        rsi_result = self.rsi.calculate(close, high, low, tr)
        
        # Combine signals: both must agree
        combined_signal = np.where(
            (mrc_result[6] < 0) & (rsi_result[6] < 0),
            -2,
            np.where((mrc_result[6] > 0) & (rsi_result[6] > 0), 2, 0)
        )
        
        return mrc_result[:-1] + (combined_signal,)
```

### Time-Based Trading Rules

Add time filters:

```python
def _get_entry_signal(self, condition: int, timestamp: datetime) -> Optional[OrderSide]:
    """Entry only during specific hours"""
    
    # Only trade during 8 AM - 4 PM UTC
    hour = timestamp.hour
    if hour < 8 or hour >= 16:
        return None
    
    # Standard logic
    if condition <= -2:
        return OrderSide.BUY
    elif condition >= 2:
        return OrderSide.SELL
    
    return None
```

## 5. Performance Optimization

### Vectorized Calculations

Use NumPy for faster calculations:

```python
# ✗ Slow: Loop-based
for i in range(len(data)):
    result[i] = data[i] * 2

# ✓ Fast: NumPy vectorized
result = data * 2
```

### Memory Optimization

For large datasets:

```python
# Load only required columns
df = pd.read_csv('data.csv', usecols=['timestamp', 'close', 'high', 'low'])

# Downsample if needed
df = df[::4]  # Use every 4th candle
```

## 6. Testing Your Customization

Create a test script:

```python
# test_custom_indicator.py
from backtester import BacktestRunner
from your_indicator import YourIndicator

def test_indicator():
    backtester = BacktestRunner("config/default_config.json")
    backtester.load_data("data/sample_data.csv")
    
    # Replace indicator
    backtester.indicator = YourIndicator()
    
    # Run backtest
    results = backtester.run_backtest()
    
    # Check results
    stats = results['statistics']
    assert stats['total_trades'] > 0, "No trades generated"
    print("✓ Tests passed")

if __name__ == "__main__":
    test_indicator()
```

## 7. Common Issues & Solutions

### No Trades Generated
- Check indicator signal calculation
- Verify condition values are -3 to 3
- Increase lookback period
- Lower take-profit percentage

### Unrealistic Results
- Check for lookahead bias (using future data)
- Verify commission calculations
- Add slippage to order fills
- Validate historical data

### Slow Performance
- Reduce data size
- Use longer timeframes
- Optimize indicator calculations
- Profile code with cProfile
