#!/usr/bin/env python
"""
Validation Script - Check if all modules are working
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backtester'))

print("="*60)
print("GRID STRATEGY BACKTESTER - VALIDATION")
print("="*60)

# Check 1: Import modules
print("\n[1/5] Checking module imports...")
try:
    from backtester.mrc_indicator import MRCIndicator
    print("  ✓ mrc_indicator.py")
    
    from backtester.order_manager import OrderManager, Order, OrderSide, OrderType
    print("  ✓ order_manager.py")
    
    from backtester.grid_engine import GridEngine, GridConfig
    print("  ✓ grid_engine.py")
    
    from backtester.backtest_runner import BacktestRunner
    print("  ✓ backtest_runner.py")
    
    from backtester.generate_sample_data import generate_sample_data
    print("  ✓ generate_sample_data.py")
    
except Exception as e:
    print(f"  ✗ Import failed: {e}")
    sys.exit(1)

# Check 2: Verify configuration file
print("\n[2/5] Checking configuration file...")
try:
    import json
    config_path = "config/default_config.json"
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            config = json.load(f)
        print(f"  ✓ Configuration loaded")
        print(f"    - Cryptocurrency: {config.get('cryptocurrency', 'N/A')}")
        print(f"    - Direction: {config.get('direction', 'N/A')}")
        print(f"    - Trading Deposit: ${config.get('trading_deposit', 'N/A')}")
    else:
        print(f"  ✗ Configuration file not found: {config_path}")
except Exception as e:
    print(f"  ✗ Configuration error: {e}")
    sys.exit(1)

# Check 3: Test MRC Indicator
print("\n[3/5] Testing MRC Indicator...")
try:
    import numpy as np
    
    # Create sample data
    length = 100
    close = np.linspace(2500, 2600, length) + np.random.normal(0, 10, length)
    high = close + np.abs(np.random.normal(0, 5, length))
    low = close - np.abs(np.random.normal(0, 5, length))
    tr = high - low
    
    # Calculate MRC
    indicator = MRCIndicator()
    meanline, meanrange, upband1, loband1, upband2, loband2, condition = indicator.calculate(
        close=close,
        high=high,
        low=low,
        true_range=tr
    )
    
    print(f"  ✓ MRC calculated")
    print(f"    - Candles: {len(close)}")
    print(f"    - Signals: {np.unique(condition).tolist()}")
    print(f"    - Mean price: ${np.mean(meanline[-10:]):.2f}")
    
except Exception as e:
    print(f"  ✗ MRC Indicator error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Check 4: Test Order Manager
print("\n[4/5] Testing Order Manager...")
try:
    from datetime import datetime
    
    om = OrderManager(commission_percent=0.1)
    
    # Create and fill orders
    order = om.create_order(
        timestamp=datetime.now(),
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        price=2500.0,
        quantity=1.0
    )
    om.fill_order(order, 2500.0, 1.0)
    
    print(f"  ✓ Order manager working")
    print(f"    - Order created: {order.order_id}")
    print(f"    - Commission: ${order.commission:.2f}")
    
except Exception as e:
    print(f"  ✗ Order Manager error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Check 5: Test Grid Engine
print("\n[5/5] Testing Grid Engine...")
try:
    grid_config = GridConfig(
        take_profit_percent=2.0,
        num_safety_orders=5,
        safety_order_step=1.5,
        martingale=1.5,
        dynamic_step=0.5,
        trading_deposit=1000.0,
        first_order_price=2500.0,
        leverage=1.0,
        direction='both'
    )
    
    engine = GridEngine(grid_config)
    print(f"  ✓ Grid engine initialized")
    
    # Try to open a position
    from datetime import datetime
    position = engine.open_position(
        timestamp=datetime.now(),
        entry_price=2500.0,
        signal_side=OrderSide.BUY
    )
    
    print(f"  ✓ Position opened")
    print(f"    - Position ID: {position.position_id}")
    print(f"    - Market order: {position.market_order.order_id}")
    print(f"    - Safety orders: {len(position.safety_orders)}")
    
except Exception as e:
    print(f"  ✗ Grid Engine error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# All tests passed
print("\n" + "="*60)
print("✓ ALL VALIDATION TESTS PASSED!")
print("="*60)
print("\nReady to run backtest. Quick start:")
print("  1. python backtester/generate_sample_data.py")
print("  2. python run_backtest.py")
print("\nOr manually:")
print("  python backtester/backtest_runner.py config/default_config.json data/sample_data.csv")
