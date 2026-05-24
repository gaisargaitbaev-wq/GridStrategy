"""
Sample Data Generator for Testing
Generates synthetic OHLCV data for backtesting
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path


def generate_sample_data(
    symbol: str = "ETHUSDT",
    start_price: float = 2500.0,
    days: int = 365,
    timeframe_minutes: int = 240,
    volatility: float = 0.02,
    trend: float = 0.0001,
    output_path: str = "../data/sample_data.csv"
) -> pd.DataFrame:
    """
    Generate synthetic OHLCV data
    
    Args:
        symbol: Trading pair
        start_price: Initial price
        days: Number of days of data
        timeframe_minutes: Candle timeframe in minutes
        volatility: Daily volatility (as decimal, e.g., 0.02 = 2%)
        trend: Daily trend (as decimal, e.g., 0.0001 = 0.01%)
        output_path: Output file path
        
    Returns:
        DataFrame with OHLCV data
    """
    
    # Calculate number of candles
    total_minutes = days * 24 * 60
    num_candles = int(total_minutes / timeframe_minutes)
    
    # Generate timestamps
    start_time = datetime(2024, 1, 1)
    timestamps = [start_time + timedelta(minutes=timeframe_minutes * i) for i in range(num_candles)]
    
    # Generate price data using random walk with drift
    prices = np.zeros(num_candles)
    prices[0] = start_price
    
    np.random.seed(42)  # For reproducibility
    
    for i in range(1, num_candles):
        # Random walk with drift (trend)
        random_change = np.random.normal(trend, volatility)
        prices[i] = prices[i-1] * (1 + random_change)
        
        # Ensure positive prices
        prices[i] = max(prices[i], 0.01)
    
    # Generate OHLC from close prices
    data = []
    for i in range(num_candles):
        close = prices[i]
        
        # Generate intracandle noise
        open_price = close * np.random.uniform(0.998, 1.002)
        high = max(open_price, close) * np.random.uniform(1.000, 1.005)
        low = min(open_price, close) * np.random.uniform(0.995, 1.000)
        
        # Generate volume
        volume = np.random.uniform(500000, 2000000)
        
        data.append({
            'timestamp': timestamps[i],
            'open': open_price,
            'high': high,
            'low': low,
            'close': close,
            'volume': int(volume)
        })
    
    df = pd.DataFrame(data)
    
    # Save to CSV
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_file, index=False)
    
    print(f"\n✓ Generated {num_candles} candles of {symbol}")
    print(f"  Timeframe: {timeframe_minutes} minutes")
    print(f"  Date range: {timestamps[0]} to {timestamps[-1]}")
    print(f"  Price range: ${prices.min():.2f} - ${prices.max():.2f}")
    print(f"  Saved to: {output_file}")
    
    return df


if __name__ == "__main__":
    # Generate sample data
    df = generate_sample_data(
        symbol="ETHUSDT",
        start_price=2500.0,
        days=365,
        timeframe_minutes=240,  # 4-hour candles
        volatility=0.02,
        trend=0.0001
    )
    
    print("\nSample data generated successfully!")
    print(df.head(10))
