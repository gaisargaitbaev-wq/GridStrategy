"""
Grid Strategy Backtester Package
"""

from .mrc_indicator import MRCIndicator
from .order_manager import Order, OrderManager, OrderSide, OrderType, Trade
from .grid_engine import GridEngine, GridConfig, GridPosition
from .backtest_runner import BacktestRunner

__version__ = "1.0.0"
__author__ = "GridStrategy Team"

__all__ = [
    "MRCIndicator",
    "Order",
    "OrderManager",
    "OrderSide",
    "OrderType",
    "Trade",
    "GridEngine",
    "GridConfig",
    "GridPosition",
    "BacktestRunner",
]
