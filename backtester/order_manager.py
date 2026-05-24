"""
Order Management System for Grid Trading
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional
from datetime import datetime
import numpy as np


class OrderType(Enum):
    """Order types"""
    MARKET = "market"
    LIMIT = "limit"


class OrderSide(Enum):
    """Order sides"""
    BUY = "buy"
    SELL = "sell"


class OrderStatus(Enum):
    """Order status"""
    PENDING = "pending"
    FILLED = "filled"
    CANCELLED = "cancelled"
    CLOSED = "closed"


@dataclass
class Order:
    """Represents a single order"""
    order_id: str
    timestamp: datetime
    side: OrderSide
    order_type: OrderType
    price: float
    quantity: float
    filled_price: Optional[float] = None
    filled_quantity: float = 0.0
    status: OrderStatus = OrderStatus.PENDING
    commission: float = 0.0
    pnl: float = 0.0
    
    def is_filled(self) -> bool:
        return self.status == OrderStatus.FILLED
    
    def is_active(self) -> bool:
        return self.status in [OrderStatus.PENDING, OrderStatus.FILLED]


@dataclass
class Trade:
    """Represents a completed trade (entry + exit)"""
    trade_id: str
    entry_order: Order
    exit_order: Order
    entry_time: datetime
    exit_time: datetime
    entry_price: float
    exit_price: float
    quantity: float
    side: OrderSide
    pnl: float
    pnl_percent: float
    is_tp_close: bool  # True if closed by take-profit
    
    def duration(self) -> int:
        """Duration in minutes"""
        return int((self.exit_time - self.entry_time).total_seconds() / 60)


class OrderManager:
    """Manages orders and trades"""
    
    def __init__(self, commission_percent: float = 0.1):
        """
        Initialize OrderManager
        
        Args:
            commission_percent: Trading commission in percentage
        """
        self.commission_percent = commission_percent
        self.orders: List[Order] = []
        self.trades: List[Trade] = []
        self.order_counter = 0
    
    def create_order(
        self,
        timestamp: datetime,
        side: OrderSide,
        order_type: OrderType,
        price: float,
        quantity: float,
        order_id: Optional[str] = None
    ) -> Order:
        """Create a new order"""
        if order_id is None:
            self.order_counter += 1
            order_id = f"ORDER_{self.order_counter}"
        
        order = Order(
            order_id=order_id,
            timestamp=timestamp,
            side=side,
            order_type=order_type,
            price=price,
            quantity=quantity
        )
        self.orders.append(order)
        return order
    
    def fill_order(
        self,
        order: Order,
        filled_price: float,
        filled_quantity: Optional[float] = None
    ) -> None:
        """Fill an order"""
        if filled_quantity is None:
            filled_quantity = order.quantity
        
        order.filled_price = filled_price
        order.filled_quantity = filled_quantity
        order.status = OrderStatus.FILLED
        order.commission = (filled_price * filled_quantity) * (self.commission_percent / 100)
    
    def cancel_order(self, order: Order) -> None:
        """Cancel an order"""
        order.status = OrderStatus.CANCELLED
    
    def close_order(self, order: Order, exit_price: float, exit_quantity: float) -> None:
        """Close an order and calculate PnL"""
        if order.side == OrderSide.BUY:
            pnl = (exit_price - order.filled_price) * exit_quantity - order.commission
        else:  # SELL
            pnl = (order.filled_price - exit_price) * exit_quantity - order.commission
        
        order.pnl = pnl
        order.status = OrderStatus.CLOSED
    
    def create_trade(
        self,
        trade_id: str,
        entry_order: Order,
        exit_order: Order,
        is_tp_close: bool = False
    ) -> Trade:
        """Create a completed trade"""
        quantity = entry_order.filled_quantity
        entry_price = entry_order.filled_price
        exit_price = exit_order.filled_price
        
        if entry_order.side == OrderSide.BUY:
            pnl = (exit_price - entry_price) * quantity
        else:  # SELL
            pnl = (entry_price - exit_price) * quantity
        
        # Subtract commissions
        total_commission = entry_order.commission + exit_order.commission
        pnl -= total_commission
        
        pnl_percent = (pnl / (entry_price * quantity)) * 100 if entry_price > 0 else 0
        
        trade = Trade(
            trade_id=trade_id,
            entry_order=entry_order,
            exit_order=exit_order,
            entry_time=entry_order.timestamp,
            exit_time=exit_order.timestamp,
            entry_price=entry_price,
            exit_price=exit_price,
            quantity=quantity,
            side=entry_order.side,
            pnl=pnl,
            pnl_percent=pnl_percent,
            is_tp_close=is_tp_close
        )
        
        self.trades.append(trade)
        return trade
    
    def get_active_orders(self, exclude_filled: bool = False) -> List[Order]:
        """Get all active orders"""
        if exclude_filled:
            return [o for o in self.orders if o.status == OrderStatus.PENDING]
        return [o for o in self.orders if o.status in [OrderStatus.PENDING, OrderStatus.FILLED]]
    
    def get_pending_orders(self) -> List[Order]:
        """Get all pending (unfilled) orders"""
        return [o for o in self.orders if o.status == OrderStatus.PENDING]
    
    def get_statistics(self) -> dict:
        """Calculate trading statistics"""
        if not self.trades:
            return {
                "total_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0,
                "win_rate": 0.0,
                "total_pnl": 0.0,
                "avg_pnl": 0.0,
                "max_pnl": 0.0,
                "min_pnl": 0.0,
                "avg_pnl_percent": 0.0
            }
        
        pnls = [t.pnl for t in self.trades]
        pnl_percents = [t.pnl_percent for t in self.trades]
        
        winning = len([t for t in self.trades if t.pnl > 0])
        losing = len([t for t in self.trades if t.pnl < 0])
        
        return {
            "total_trades": len(self.trades),
            "winning_trades": winning,
            "losing_trades": losing,
            "win_rate": (winning / len(self.trades) * 100) if self.trades else 0.0,
            "total_pnl": sum(pnls),
            "avg_pnl": np.mean(pnls) if pnls else 0.0,
            "max_pnl": max(pnls) if pnls else 0.0,
            "min_pnl": min(pnls) if pnls else 0.0,
            "avg_pnl_percent": np.mean(pnl_percents) if pnl_percents else 0.0
        }
