#!/usr/bin/env python
"""
Quick Start Script - Generate sample data and run backtest
"""
import sys
import os

# Use package imports for the backtester module
sys.path.insert(0, os.path.dirname(__file__))

from backtester.generate_sample_data import generate_sample_data
from backtester.backtest_runner import BacktestRunner


def main():
    print("="*60)
    print("GRID STRATEGY BACKTESTER - QUICK START")
    print("="*60)
    
    # Step 1: Generate sample data
    print("\n1. Generating sample OHLCV data...")
    print("   (You can replace this with real data from CSV)")
    
    sample_data = generate_sample_data(
        symbol="ETHUSDT",
        start_price=2500.0,
        days=365,
        timeframe_minutes=240,  # 4-hour candles
        volatility=0.02,
        trend=0.0001,
        output_path="data/sample_ETHUSDT_4h.csv"
    )
    
    # Step 2: Run backtest
    print("\n2. Running backtest with sample data...")
    print("   (Using default_config.json)")
    
    try:
        backtester = BacktestRunner("config/default_config.json")
        backtester.load_data("data/sample_ETHUSDT_4h.csv")
        results = backtester.run_backtest()
        
        # Save results
        backtester.save_results("results/backtest_results.json")
        backtester.save_data_with_indicators("results/data_with_indicators.csv")
        
        # Print summary
        backtester.print_summary()
        
        print("\n✓ Backtest completed successfully!")
        print(f"\nResults saved to:")
        print(f"  - results/backtest_results.json")
        print(f"  - results/data_with_indicators.csv")
        
    except Exception as e:
        print(f"\n✗ Error running backtest: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
